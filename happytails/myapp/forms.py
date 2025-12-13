from django import forms
from .models import Animal

class AnimalForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = ['name', 'age', 'breed', 'story', 'image', 'status'] 
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numele animalului'}),
            'age': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vârsta'}),
            'breed': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rasa'}),
            'story': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Povestea animalului...'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }