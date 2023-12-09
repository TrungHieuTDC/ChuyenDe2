from django import forms
from .models import PostImage,Post,Group,PostVideo,Profile
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
class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description','avatar','background_image', 'access','post_approval_enabled']
    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
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
        model = PostImage
        fields = ['images']
class PostImageForm(forms.Form):
    class Meta:
        model = PostImage
        fields = ['image']
class VideoForm(forms.ModelForm):
    class Meta:
        model = PostVideo
        fields = ['video']
class EditGroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'avatar', 'background_image', 'access','post_approval_enabled']
    def __init__(self, *args, **kwargs):
        super(EditGroupForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'    
class BackgroundAvatarForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['background_avatar']