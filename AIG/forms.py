from django import forms

class AIGForm(forms.Form):
	users = forms.FloatField()
	bandwidth = forms.FloatField()
	eventmarking = forms.FloatField()
	eventtimestamp = forms.CharField(max_length=100)
