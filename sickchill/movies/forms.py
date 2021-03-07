from wtforms_alchemy import ModelForm, ModelFormMeta

from .models import Qualities


class QualitiesForm(ModelForm):
    class Meta:
        model = Qualities
        include_primary_keys = True
        include_foreign_keys = True
