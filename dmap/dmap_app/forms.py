from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
import phonenumbers
from .models import Utilisateur

class UtilisateurForm(forms.ModelForm):
    pays = CountryField().formfield(widget=CountrySelectWidget(attrs={'class': 'form-control'}))
    telephone = forms.CharField(max_length=25, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Utilisateur
        fields = ['pays', 'telephone']

    def clean_telephone(self):
        phone = self.cleaned_data.get('telephone')
        code_country = self.cleaned_data.get('pays')

        if code_country:
            # Ajouter l'indicatif du pays sélectionné
            numero_complet = phonenumbers.parse(phone, code_country)

            if not phonenumbers.is_valid_number(numero_complet):
                raise forms.ValidationError("Numéro de téléphone invalide.")

        return phone
