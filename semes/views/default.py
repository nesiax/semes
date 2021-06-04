"""
default views
"""

from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound
from pyramid.settings import asbool

import colander
import deform.widget
from deform.widget import Invalid

import gammu.smsd
import phonenumbers

@view_config(route_name='home')
def home(request):
    """ home """
    url = request.route_url('send')
    return HTTPFound(location=url)


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


@view_defaults(route_name='send', renderer='../templates/send.xhtml')
class Send:
    """ Send SMS """


    def lenok(self, text, **settings):
        """ checks to make sure is text is valid lenght """

        ascii_length = int(settings.get('ascii_length', self.ascii_length))
        unicode_length = int(settings.get('unicode_length', self.unicode_length))
        multipart = asbool(settings.get("semes.multipart", self.multipart))

        #import pdb;  pdb.set_trace()

        status = False
        msg = None

        if multipart is False:

            if text.isascii():
                if len(text) > ascii_length:
                    msg = ('ASCII message length is %s ' \
                           'and exceeds %s characters limit.') \
                           % (len(text), ascii_length)
                else:
                    status = True
            else:
                if len(text) > unicode_length:
                    msg = ('UTF-8 message length is %s ' \
                           'and exceeds %s characters limit.') \
                           % (len(text), unicode_length)
                else:
                    status = True
        else:
            status = True

        return {'status': status, 'msg': msg}



    @staticmethod
    def _form():
        """ form for sending sms message"""

        class Schema(colander.Schema):
            """ sms schema """
            phone = colander.SchemaNode(
                colander.String(),
                title="Phone number",
                description="Type the phone number",
                validator=phoneok,
                widget=deform.widget.TextInputWidget(
                    attributes={
                        "placeholder": "+570001112222",
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
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return form

    def __init__(self, request):
        self.request = request
        self.smsd = gammu.smsd.SMSD('/etc/gammu-smsdrc')
        self.form = self._form()

        self.ascii_length = int(request.registry.settings.get(
            'semes.ascii_length',160))
        self.unicode_length = int(request.registry.settings.get(
            'semes.unicode_length', 58))
        self.multipart = asbool(request.registry.settings.get(
            'semes.multipart', False))
        self.maxparts = int(request.registry.settings.get(
            'semes.maxparts', 2))

        inline_css = """

"""
        self.response = {
            'reqts' : self.form.get_widget_resources(),
            "status": False,
            'title' : "Send Message",
            '_inline_css': inline_css,
        }


    @view_config(request_method="GET")
    def get(self):
        """ get """

        self.response.update({
            'form_rendered' : self.form.render(),
        })

        return self.response


    @view_config(request_method="POST")
    def post(self):
        """ post """

        appstruct = {}
        message = ''
        controls = self.request.POST.items()

        try:
            appstruct = self.form.validate(controls)
            message =  appstruct['message']
            e164_phone = phonenumbers.\
                format_number(phonenumbers.parse(appstruct['phone'], None),
                              phonenumbers.PhoneNumberFormat.E164)
        except deform.ValidationFailure:
            self.response.update({
                'form_rendered' : self.form.render(),
            })
            return self.response

        # custom validation
        res_lenok = self.lenok(message)
        if res_lenok['status'] is False:
            self.form.error = colander.Invalid(self.form)
            self.form['message'].error = colander.Invalid(self.form['message'],
                                                          res_lenok['msg'])
            self.response.update({
                'form_rendered' : self.form.render(appstruct),
            })
            return self.response

        entry_id = 'ConcatenatedTextLong' \
        if self.multipart is True and \
           ((message.isascii() and len(message) > self.ascii_length or
            not message.isascii() and len(message) > self.unicode_length)) \
        else 'Text'

        smsinfo = {
            'Unicode': not message.isascii(),
            'Entries':  [
                {   'ID': entry_id,
                    'Buffer': message
                }
            ]}

        encoded = gammu.EncodeSMS(smsinfo)

        #import pdb;  pdb.set_trace()

        # Text that span more than one message
        if entry_id == 'Text' and len(encoded) > 1:
            error = \
                ('Message length is %s in charset %s and generates %s messages.'
                 ' Please adjust your settings.') \
                 % (len(message),
                    'ASCII' if message.isascii() else 'Unicode',
                    len(encoded))
            self.form.error = colander.Invalid(self.form)
            self.form['message'].error = colander.Invalid(self.form['message'],
                                                          error)

            self.response.update({
                'form_rendered' : self.form.render(appstruct),
            })
            return self.response

        # ASCII messages truncated
        if entry_id == 'Text' and len(encoded) == 1 \
           and encoded[0]['Length'] < len(message):
            error =  'Message length is %s in charset %s and truncated at %s' \
                % (len(message),
                   'ASCII' if message.isascii() else 'Unicode',
                   encoded[0]['Length'])
            self.form.error = colander.Invalid(self.form['message'])
            self.form['message'].error = colander.Invalid(self.form['message'],
                                                          error)

            self.response.update({
                'form_rendered' : self.form.render(appstruct),
            })
            return self.response

        # Maxparts message exceded
        if entry_id == 'ConcatenatedTextLong' and len(encoded) > self.maxparts:
            error = \
                ('Message parts length is %s in charset %s '
                 'and exceeds %s limit .') \
                 % (len(encoded),
                    'ASCII' if message.isascii() else 'Unicode',
                    self.maxparts)
            self.form.error = colander.Invalid(self.form['message'])
            self.form['message'].error = colander.Invalid(self.form['message'],
                                                          error)

            self.response.update({
                'form_rendered' : self.form.render(appstruct),
            })
            return self.response

        # Send messages
        submission_ids = []
        for msgstruct in encoded:
            # Fill in numbers
            msgstruct['SMSC'] = {'Location': 1}
            msgstruct['Number'] = e164_phone

            #print(len(message))
            #print(msgstruct)

            # Send the msgstruct
            submission_ids.append (self.smsd.InjectSMS([msgstruct]))

        # Renew form
        del self.form
        self.form = self._form()
        self.response.update({
            'status' : True,
            'form_rendered' : self.form.render(),
            'submission_ids': submission_ids,
            'e164_phone' : e164_phone,
        })

        return self.response
