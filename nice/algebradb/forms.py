from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(label="Выберите txt-файл для загрузки")
    family = forms.IntegerField(label="Введите номер семьи", min_value=1)

class DeleteForm(forms.Form):
    n_param = forms.IntegerField(label="n_param", required=False)
    a_param = forms.IntegerField(label="a_param", required=False) #поменять потом
    sekvens = forms.CharField(label="sekvens", max_length=100, required=False)
    family = forms.IntegerField(label="family", min_value=1, required=True)

    def clean(self):
        cleaned = super().clean()
        n = cleaned.get("n_param")
        a = cleaned.get("a_param")
        s = cleaned.get("sekvens")
        f = cleaned.get("family")

        # family обязателен всегда
        if f is None:
            raise forms.ValidationError("Необходимо указать параметр family.")

        # если указали n_param или a_param — оба должны быть
        if (n is not None or a is not None) and not (n is not None and a is not None):
            raise forms.ValidationError("Для удаления по n_param и a_param необходимо заполнить оба поля.")

        # нельзя одновременно указывать sekvens и (n_param/a_param)
        if s and (n is not None or a is not None):
            raise forms.ValidationError("Нельзя указывать одновременно sekvens и n_param/a_param. Выберите одно условие.")

        return cleaned

class SubseqForm(forms.Form):
    subseq = forms.CharField()  