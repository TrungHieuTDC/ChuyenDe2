from django import forms
from .models import *
from django.forms import ClearableFileInput
from ckeditor.widgets import CKEditorWidget
class PostTextForm(forms.Form):
    content = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'Write something here...', 'style': 'border:none'}))

class BasicCKEditorWidget(CKEditorWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['toolbar'] = [
        ['Bold', 'Italic', 'Underline'],
        
]

class PostForm(forms.ModelForm):
    class Meta:
        model = PostUser
        fields = ['content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Title of the Post'}),
            'content': BasicCKEditorWidget(),
        }
class PostImageEditForm(forms.Form):
    image = forms.ImageField(widget=forms.ClearableFileInput(attrs={
        'class': 'bg-soft-primary rounded p-2 pointer me-3',
        'type': 'file',
        'accept': 'image/*',
        'placeholder': 'Choose an Image',
    }))
    class Meta:
        model = PostImageUser
        fields = ['images']
class PostImageForm(forms.Form):
    class Meta:
        model = PostImageUser
        fields = ['image']
class VideoForm(forms.ModelForm):
    class Meta:
        model = PostVideoUser
        fields = ['video']
class PostPrivacyForm(forms.Form):
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('friend', 'Friends Only'),
        ('private', 'Private'),
    ]

    privacy = forms.ChoiceField(choices=PRIVACY_CHOICES, widget=forms.RadioSelect())

