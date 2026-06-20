from django import forms

class PriceProposalForm(forms.Form):
    suggested_price = forms.DecimalField(max_digits=10, decimal_places=2)
    message = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows":2}))

class SendMessageForm(forms.Form):
    text = forms.CharField(max_length=500, widget=forms.Textarea(attrs={"rows":3}))