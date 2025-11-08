from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    
    class Meta:
        model = Event
        fields = [
            'name', 'date', 'start_time', 'end_time', 'location',
            'organizer', 'capacity', 'price', 'dress_code'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'dress_code': forms.TextInput(attrs={'type': 'color'}),  # <-- color picker
        }
