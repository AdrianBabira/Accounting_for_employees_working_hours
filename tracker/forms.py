from django import forms

from .models import Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"placeholder": "Например, Анна Иванова"})}

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Введите имя сотрудника.")
        return name


class WorkEntryForm(forms.Form):
    description = forms.CharField(
        max_length=200,
        label="Описание задачи",
        widget=forms.TextInput(attrs={"placeholder": "Например, подготовка отчёта"}),
    )


class ReportFilterForm(forms.Form):
    date_from = forms.DateField(
        label="С",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        input_formats=["%Y-%m-%d"],
    )
    date_to = forms.DateField(
        label="По",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        input_formats=["%Y-%m-%d"],
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        label="Сотрудник",
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("Начало периода не может быть позже его окончания.")
        return cleaned_data
