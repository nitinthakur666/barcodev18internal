import ast
import base64
import datetime
import logging
import psycopg2
import smtplib
import threading
import re
import pytz

from collections import defaultdict
from dateutil.parser import parse

from odoo import _, api, fields, models, modules
from odoo import tools
from odoo.addons.base.models.ir_mail_server import MailDeliveryException

_logger = logging.getLogger(__name__)


class Mail(models.Model):
    _inherit = 'mail.mail'
    
    email_bcc = fields.Char("BCC")

    def _send(self, auto_commit=False, raise_exception=False, smtp_session=None, alias_domain_id=False,
              mail_server=False, post_send_callback=None):
        IrMailServer = self.env['ir.mail_server']
        # Only retrieve recipient followers of the mails if needed
        mails_with_unfollow_link = self.filtered(lambda m: m.body_html and '/mail/unfollow' in m.body_html)
        recipients_follower_status = (
            None if not mails_with_unfollow_link
            else self.env['mail.followers']._get_mail_recipients_follower_status(mails_with_unfollow_link.ids)
        )

        for mail_id in self.ids:
            success_pids = []
            failure_reason = None
            failure_type = None
            mail = None
            try:
                mail = self.browse(mail_id)
                if mail.state != 'outgoing':
                    continue

                # Writing on the mail object may fail (e.g. lock on user) which
                # would trigger a rollback *after* actually sending the email.
                # To avoid sending twice the same email, provoke the failure earlier
                mail.write({
                    'state': 'exception',
                    'failure_reason': _('Error without exception. Probably due to sending an email without computed recipients.'),
                })
                # Update notification in a transient exception state to avoid concurrent
                # update in case an email bounces while sending all emails related to current
                # mail record.
                notifs = self.env['mail.notification'].search([
                    ('notification_type', '=', 'email'),
                    ('mail_mail_id', 'in', mail.ids),
                    ('notification_status', 'not in', ('sent', 'canceled'))
                ])
                if notifs:
                    notif_msg = _('Error without exception. Probably due to concurrent access update of notification records. Please see with an administrator.')
                    notifs.sudo().write({
                        'notification_status': 'exception',
                        'failure_type': 'unknown',
                        'failure_reason': notif_msg,
                    })
                    # `test_mail_bounce_during_send`, force immediate update to obtain the lock.
                    # see rev. 56596e5240ef920df14d99087451ce6f06ac6d36
                    notifs.flush_recordset(['notification_status', 'failure_type', 'failure_reason'])

                # protect against ill-formatted email_from when formataddr was used on an already formatted email
                emails_from = tools.mail.email_split_and_format_normalize(mail.email_from)
                email_from = emails_from[0] if emails_from else mail.email_from

                # build an RFC2822 email.message.Message object and send it without queuing
                res = None
                # TDE note: could be great to pre-detect missing to/cc and skip sending it
                # to go directly to failed state update
                email_list = mail._prepare_outgoing_list(
                    mail_server=mail_server or mail.mail_server_id,
                    recipients_follower_status=recipients_follower_status,
                )

                # send each sub-email
                for email in email_list:
                    # give indication to 'send_mail' about emails already considered
                    # as being valid
                    email_to_normalized = email.pop('email_to_normalized', [])
                    # if given, contextualize sending using alias domains
                    if alias_domain_id:
                        alias_domain = self.env['mail.alias.domain'].sudo().browse(alias_domain_id)
                        SendIrMailServer = IrMailServer.with_context(
                            domain_notifications_email=alias_domain.default_from_email,
                            domain_bounce_address=email['headers'].get('Return-Path') or alias_domain.bounce_email,
                            send_validated_to=email_to_normalized,
                        )
                    else:
                        SendIrMailServer = IrMailServer.with_context(send_validated_to=email_to_normalized)
                    msg = SendIrMailServer.build_email(
                        email_from=email_from,
                        email_to=email['email_to'],
                        subject=email['subject'],
                        body=email['body'],
                        body_alternative=email['body_alternative'],
                        email_cc=email['email_cc'],
                        email_bcc=email['email_bcc'],
                        reply_to=email['reply_to'],
                        attachments=email['attachments'],
                        message_id=email['message_id'],
                        references=email['references'],
                        object_id=email['object_id'],
                        subtype='html',
                        subtype_alternative='plain',
                        headers=email['headers'],
                    )
                    processing_pid = email.pop("partner_id", None)
                    try:
                        res = SendIrMailServer.send_email(
                            msg, mail_server_id=mail.mail_server_id.id, smtp_session=smtp_session)
                        if processing_pid:
                            success_pids.append(processing_pid)
                        processing_pid = None
                    except AssertionError as error:
                        if str(error) == IrMailServer.NO_VALID_RECIPIENT:
                            # if we have a list of void emails for email_list -> email missing, otherwise generic email failure
                            if not email.get('email_to') and failure_type != "mail_email_invalid":
                                failure_type = "mail_email_missing"
                            else:
                                failure_type = "mail_email_invalid"
                            # No valid recipient found for this particular
                            # mail item -> ignore error to avoid blocking
                            # delivery to next recipients, if any. If this is
                            # the only recipient, the mail will show as failed.
                            _logger.info("Ignoring invalid recipients for mail.mail %s: %s",
                                         mail.message_id, email.get('email_to'))
                        else:
                            raise
                if res:  # mail has been sent at least once, no major exception occurred
                    mail.write({'state': 'sent', 'message_id': res, 'failure_reason': False})
                    if not modules.module.current_test:
                        _logger.info(
                            "Mail (mail.mail) with ID %r and Message-Id %r from %r to (redacted) %s successfully sent",
                            mail.id,
                            mail.message_id,
                            tools.email_normalize(msg['from']),  # FROM should not change, so last msg good enough
                            ', '.join(
                                repr(tools.mail.email_anonymize(tools.email_normalize(m['email_to'])))
                                for m in email_list
                            ),
                        )
                        _logger.info("Total emails tried by SMTP: %s", len(email_list))

                    # /!\ can't use mail.state here, as mail.refresh() will cause an error
                    # see revid:odo@openerp.com-20120622152536-42b2s28lvdv3odyr in 6.1
                mail._postprocess_sent_message(success_pids=success_pids, failure_type=failure_type)
            except MemoryError:
                # prevent catching transient MemoryErrors, bubble up to notify user or abort cron job
                # instead of marking the mail as failed
                _logger.exception(
                    'MemoryError while processing mail with ID %r and Msg-Id %r. Consider raising the --limit-memory-hard startup option',
                    mail.id, mail.message_id)
                # mail status will stay on ongoing since transaction will be rollback
                raise
            except (psycopg2.Error, smtplib.SMTPServerDisconnected):
                # If an error with the database or SMTP session occurs, chances are that the cursor
                # or SMTP session are unusable, causing further errors when trying to save the state.
                _logger.exception(
                    'Exception while processing mail with ID %r and Msg-Id %r.',
                    mail.id, mail.message_id)
                raise
            except Exception as e:
                if isinstance(e, AssertionError):
                    # Handle assert raised in IrMailServer to try to catch notably from-specific errors.
                    # Note that assert may raise several args, a generic error string then a specific
                    # message for logging in failure type
                    error_code = e.args[0]
                    if len(e.args) > 1 and error_code == IrMailServer.NO_VALID_FROM:
                        # log failing email in additional arguments message
                        failure_reason = str(e.args[1])
                    else:
                        failure_reason = error_code
                    if error_code == IrMailServer.NO_VALID_FROM:
                        failure_type = "mail_from_invalid"
                    elif error_code in (IrMailServer.NO_FOUND_FROM, IrMailServer.NO_FOUND_SMTP_FROM):
                        failure_type = "mail_from_missing"
                # generic (unknown) error as fallback
                if not failure_reason:
                    failure_reason = tools.exception_to_unicode(e)
                if not failure_type:
                    failure_type = "unknown"

                _logger.exception('failed sending mail (id: %s) due to %s', mail.id, failure_reason)
                mail.write({
                    "failure_reason": failure_reason,
                    "failure_type": failure_type,
                    "state": "exception",
                })
                mail._postprocess_sent_message(
                    success_pids=success_pids,
                    failure_reason=failure_reason, failure_type=failure_type
                )
                if raise_exception:
                    if isinstance(e, (AssertionError, UnicodeEncodeError)):
                        if isinstance(e, UnicodeEncodeError):
                            value = "Invalid text: %s" % e.object
                        else:
                            value = '. '.join(e.args)
                        raise MailDeliveryException(value)
                    raise
            if auto_commit is True:
                if post_send_callback:
                    post_send_callback([mail_id])
                self._cr.commit()
            mail.invalidate_recordset(['body_html'])
        if post_send_callback:
            post_send_callback(self.ids)
        return True

    def _prepare_outgoing_list(self, mail_server=False, recipients_follower_status=None):
        """ Return a list of emails to send based on current mail.mail. Each
        is a dictionary for specific email values, depending on a partner, or
        generic to the whole recipients given by mail.email_to.

        :param mail_server: <ir.mail_server> mail server that will be used to send the mails,
          False if it is the default one
        :param set recipients_follower_status: see ``Followers._get_mail_recipients_follower_status()``
        :return list: list of dicts used in IrMailServer.build_email()
        """
        self.ensure_one()
        body = self._prepare_outgoing_body()

        # headers
        headers = {}
        if self.headers:
            try:
                headers = ast.literal_eval(self.headers)
            except (ValueError, TypeError) as e:
                _logger.warning(
                    'Evaluation error when evaluating mail headers (received %r): %s',
                    self.headers, e,
                )
            # global except as we don't want to crash the queue just due to a malformed
            # headers value
            except Exception as e:
                _logger.warning(
                    'Unknown error when evaluating mail headers (received %r): %s',
                    self.headers, e,
                )
        headers.setdefault('Return-Path', self.record_alias_domain_id.bounce_email or self.env.company.bounce_email)

        # prepare recipients: use email_to if defined then check recipient_ids
        # that receive a specific email, notably due to link shortening / redirect
        # that is recipients-dependent. Keep original email/partner as this is
        # used in post-processing to know failures, like missing recipients
        email_list = []
        if self.email_to:
            email_to_normalized = tools.mail.email_normalize_all(self.email_to)
            email_to = tools.mail.email_split_and_format_normalize(self.email_to)
            email_list.append({
                'email_cc': [],
                'email_bcc': [],
                'email_to': email_to,
                # list of normalized emails to help extract_rfc2822
                'email_to_normalized': email_to_normalized,
                # keep raw initial value for incoming pre processing of outgoing emails
                'email_to_raw': self.email_to or '',
                'partner_id': False,
            })
        # add all cc once, either to the first "To", either as a single entry (do not mix
        # with partner-specific sending)
        if self.email_cc:
            if email_list:
                email_list[0]['email_cc'] = tools.mail.email_split_and_format_normalize(self.email_cc)
                email_list[0]['email_to_normalized'] += tools.mail.email_normalize_all(self.email_cc)
            else:
                email_list.append({
                    'email_cc':  tools.mail.email_split_and_format_normalize(self.email_cc),
                    'email_bcc': [],
                    'email_to': [],
                    'email_to_normalized': tools.mail.email_normalize_all(self.email_cc),
                    'email_to_raw': False,
                    'partner_id': False,
                })

        if self.email_bcc:
            if email_list:
                email_list[0]['email_bcc'] = tools.mail.email_split_and_format_normalize(self.email_bcc)
                email_list[0]['email_to_normalized'] += tools.mail.email_normalize_all(self.email_bcc)
            else:
                email_list.append({
                    'email_cc': [],
                    'email_bcc':  tools.mail.email_split_and_format_normalize(self.email_bcc),
                    'email_to': [],
                    'email_to_normalized': tools.mail.email_normalize_all(self.email_bcc),
                    'email_to_raw': False,
                    'partner_id': False,
                })
        # specific behavior to customize the send email for notified partners
        for partner in self.recipient_ids:
            # check partner email content
            email_to_normalized = tools.mail.email_normalize_all(partner.email)
            email_to = [
                tools.formataddr((partner.name or "", email or "False"))
                for email in email_to_normalized or [partner.email]
            ]
            email_list.append({
                'email_cc': [],
                'email_bcc': [],
                'email_to': email_to,
                # list of normalized emails to help extract_rfc2822
                'email_to_normalized': email_to_normalized,
                # keep raw initial value for incoming pre processing of outgoing emails
                'email_to_raw': partner.email or '',
                'partner_id': partner,
            })

        attachments = self.attachment_ids
        # Prepare attachments:
        # Remove attachments if user send the link with the access_token.
        if body and attachments:
            link_ids = {int(link) for link in re.findall(r'/web/(?:content|image)/([0-9]+)', body)}
            if link_ids:
                attachments = attachments - self.env['ir.attachment'].browse(list(link_ids))

        # Convert URL-only attachments (e.g. cloud or plain external links) into email links
        url_attachments = attachments.sudo().filtered(
            lambda a: a.url and not a.file_size and a.url.startswith(('http://', 'https://', 'ftp://')))
        if url_attachments:
            url_attachments.sudo().generate_access_token()
            attachments_links = self.env['ir.qweb']._render('mail.mail_attachment_links', {'attachments': url_attachments})
            body = tools.mail.append_content_to_html(body, attachments_links, plaintext=False)
            attachments -= url_attachments

        # Turn remaining attachments into links if they are too heavy and
        # their ownership are business models (i.e. something != mail.message,
        # otherwise they will be deleted along with the mail message leading to a 404)
        if record_owned_attachments := attachments.sudo().filtered(
                lambda a: a.res_model and a.res_id and a.res_model != 'mail.message'):
            estimated_email_size_bytes = self._estimate_email_size(
                headers, body, [a.file_size for a in attachments.sudo()])
            max_email_size_bytes = (mail_server or self.env['ir.mail_server']
                                    ).sudo()._get_max_email_size() * 1024 * 1024
            if estimated_email_size_bytes > max_email_size_bytes:
                # Remove attachments and prepare downloadable links to be added in the body
                record_owned_attachments.sudo().generate_access_token()
                attachments_links = self.env['ir.qweb']._render('mail.mail_attachment_links',
                                                                {'attachments': record_owned_attachments})
                body = tools.mail.append_content_to_html(body, attachments_links, plaintext=False)
                attachments -= record_owned_attachments
        # Prepare the remaining attachment (those not embedded as link)
        # load attachment binary data with a separate read(), as prefetching all
        # `datas` (binary field) could bloat the browse cache, triggering
        # soft/hard mem limits with temporary data.
        email_attachments = [(a['name'], a['raw'], a['mimetype'])
                             for a in attachments.sudo().read(['name', 'raw', 'mimetype'])
                             if a['raw'] is not False]

        # Build final list of email values with personalized body for recipient
        results = []
        for email_values in email_list:
            partner_id = email_values['partner_id']
            body_personalized = self._personalize_outgoing_body(body, partner_id, recipients_follower_status)
            results.append({
                'attachments': email_attachments,
                'body': body_personalized,
                'body_alternative': tools.html2plaintext(body_personalized),
                'email_cc': email_values['email_cc'],
                'email_bcc': email_values['email_bcc'],
                'email_from': self.email_from,
                'email_to': email_values['email_to'],
                'email_to_normalized': email_values['email_to_normalized'],
                'email_to_raw': email_values['email_to_raw'],
                'headers': headers,
                'message_id': self.message_id,
                'object_id': f'{self.res_id}-{self.model}' if self.res_id else '',
                'partner_id': partner_id,
                'references': self.references,
                'reply_to': self.reply_to,
                'subject': self.subject,
            })

        return results