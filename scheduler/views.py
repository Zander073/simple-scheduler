from django.shortcuts import render
from django.views.generic import TemplateView


class SchedulerView(TemplateView):
    template_name = 'scheduler/index.html'
