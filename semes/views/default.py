"""
default views
"""

import logging
import colander
import deform.widget

from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound
#from pyramid.settings import asbool

from deform.widget import Invalid

import gammu.smsd
import phonenumbers

LOG = logging.getLogger(__name__)

@view_config(route_name='home')
def home(request):
    """ home """
    url = request.route_url('send')
    return HTTPFound(location=url)


def encodeSMS(message): # pylint: disable=invalid-name
    """ encode message to SMS """

    entry_id = 'ConcatenatedTextLong'

    smsinfo = {
        'Unicode': not message.isascii(),
        'Entries':  [
            {   'ID': entry_id,
                'Buffer': message
            }
        ]}

    encoded = gammu.EncodeSMS(smsinfo) # pylint: disable=no-member

    return encoded

def sendSMS(encoded, smsdrc, e164_phone): # pylint: disable=invalid-name
    """ Send SMS """

    smsd = gammu.smsd.SMSD(smsdrc)

    submission_ids = []

    for msgstruct in encoded:
        # Fill in numbers
        msgstruct['SMSC'] = {'Location': 1}
        msgstruct['Number'] = e164_phone

        # Send the msgstruct
        submission_ids.append (smsd.InjectSMS([msgstruct]))

    return submission_ids


class SendForm():
    """ Send Form """

    def __init__(self, max_parts):
        """ form for sending sms message"""

        class Schema(colander.Schema):
            """ sms schema """

            phone = colander.SchemaNode(
                colander.String(),
                title="Phone number",
                description="Type the phone number",
                preparer=SendForm.prepare_phone,
                validator=SendForm.phoneok,
                widget=deform.widget.TextInputWidget(
                    attributes={
                        "placeholder": "+573223334444",
                    }),
            )

            message = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.TextAreaWidget(
                    rows=10, cols=60,
                    attributes={
                        "placeholder": "Type some message.",
                    }),
                description="Enter some text",
                validator=colander.All(SendForm.lenok),
                settings={'max_parts': max_parts,},
            )

        schema = Schema()

        #import pdb;  pdb.set_trace()

        self.form = deform.Form(schema, buttons=("submit",))


    @staticmethod
    def prepare_phone(value):
        """ return fake """
        #import pdb;  pdb.set_trace()
        try:
            phone =  phonenumbers.\
                format_number(phonenumbers.parse(value, None),
                              phonenumbers.PhoneNumberFormat.E164)
            return phone
        except Exception as exc: # pylint: disable=broad-except
            LOG.debug(exc)
            return value

    @staticmethod
    def phoneok(node, value):
        """ checks to make sure is a valid phone number """
        try:
            phone = phonenumbers.parse(value, None)

            if phonenumbers.is_possible_number(phone) \
               and phonenumbers.is_valid_number(phone):
                return None

            raise Invalid(node,
                          '%s is not a valid phone number' % value)

        except phonenumbers.phonenumberutil.NumberParseException as exc:
            raise Invalid(node,
                          '%s is not a valid phone number' % value) from exc

    @staticmethod
    def lenok(node, value):
        """ checks to make sure is value is valid lenght """

        # import pdb;  pdb.set_trace()

        max_parts = node.settings['max_parts']

        encoded = encodeSMS(value)

        len_parts = len (encoded)
        len_chars = sum ([message['Length'] for message in encoded] )

        if len_parts > max_parts:
            error = \
                ('Maximum SMS per message is %s. ' + \
                 'Your message span %s SMS and have %s characters.') \
                 % (max_parts, len_parts, len_chars)

            raise Invalid(node, error)


@view_defaults(route_name='send', renderer='../templates/send.xhtml')
class Send:
    """ Send SMS """

    def __init__(self, request):
        self.request = request
        self.smsdrc = request.registry.settings.get('semes.smsdrc',
                                                    '/etc/gammu-smsdrc')
        self.max_parts = int(
            request.registry.settings.get('semes.max_parts', 2))

        self.form = self._form()

        inline_css = """
"""
        self.response = {
            'reqts' : self.form.get_widget_resources(),
            "status": False,
            'title' : "Send Message",
            '_inline_css': inline_css,
        }


    def _form(self):
        """ return a new instance of SendForm """
        return SendForm(self.max_parts).form

    @view_config(request_method="GET")
    def get(self):
        """ get """

        self.response.update({
            'form_rendered' : self.form.render(),
        })

        return self.response


    @view_config(request_method="POST", xhr=True, renderer="json")
    @view_config(request_method="POST")
    def post(self):
        """ post """

        appstruct = {}
        message = ''
        controls = self.request.POST.items()

        try:
            appstruct = self.form.validate(controls)
            message =  appstruct['message']
            e164_phone = appstruct['phone']

        except deform.ValidationFailure as exc:

            response = {'status':False, 'errors': exc.error.asdict()}

            if self.request.is_xhr:
                return response

            response['form_rendered'] = self.form.render()
            self.response.update(response)

            return self.response

        encoded = encodeSMS(message)
        submission_ids = sendSMS(encoded, self.smsdrc, e164_phone)

        response = {
            'status' : True,
            'submission_ids': submission_ids,
            'e164_phone' : e164_phone,
        }

        # import pdb;  pdb.set_trace() # pylint: disable=import-outside-toplevel, multiple-statements

        if self.request.is_xhr:
            return response

        # Renew form
        response['form_rendered'] = self._form().render()

        self.response.update(response)

        return self.response
