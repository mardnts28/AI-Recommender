from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    # Manual tags input as comma-separated text
    tags_input = forms.CharField(
        required=False,
        label="Tags",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. electronics, wireless, portable'
        }),
        help_text="Optional: separate tags with commas. AI will also auto-generate tags."
    )

    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'tags_input']