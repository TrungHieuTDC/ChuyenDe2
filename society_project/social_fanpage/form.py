from django import forms
from social_fanpage.models import *
from django.forms import ClearableFileInput
from ckeditor.widgets import CKEditorWidget
class BasicCKEditorWidget(CKEditorWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['toolbar'] = [
        ['Bold', 'Italic', 'Underline'],
        
]      
class FanPageForm(forms.ModelForm):
    class Meta:
        model = Fanpage
        fields = ['name', 'description','avatar','cover_image','is_hidden']
    def __init__(self, *args, **kwargs):
        super(FanPageForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
class PostForm(forms.ModelForm):
    class Meta:
        model = FanpagePost
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
        model = PostImageFanpage
        fields = ['images']
class PostImageForm(forms.Form):
    class Meta:
        model = PostImageFanpage
        fields = ['image']
class VideoForm(forms.ModelForm):
    class Meta:
        model = PostVideoFanpage
        fields = ['video']