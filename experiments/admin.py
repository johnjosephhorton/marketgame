from django.contrib import admin

from experiments.models import (Experiment,
                                Participant,
                                Session,
                                Event,
                                Item,
                                ChoiceSet,
                                Winner)


class ExperimentAdmin(admin.ModelAdmin):
    pass


class ParticipantAdmin(admin.ModelAdmin):
    pass


class SessionAdmin(admin.ModelAdmin):
    pass


class EventAdmin(admin.ModelAdmin):
    pass


class ItemAdmin(admin.ModelAdmin):
    pass


class ChoiceSetAdmin(admin.ModelAdmin):
    pass


class WinnerAdmin(admin.ModelAdmin):
    pass


admin.site.register(Experiment, ExperimentAdmin)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(ChoiceSet, ChoiceSetAdmin)
admin.site.register(Winner, WinnerAdmin)
