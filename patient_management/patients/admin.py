from django.contrib import admin
from .models import (
    Patient, 
    PatientHistory, 
    NewRecommendationsStage, 
    FollowUpStage, 
    ClinicalInterventionStage, 
    QuotationPhaseStage, 
    ReadyToScheduleStage, 
    PreAdmissionPrepStage, 
    PostponedAdmissionsStage, 
    ClinicalStage, 
    InitialTransitionStage, 
    FinalTransitionStage, 
    ClosedStage,
    CohortAStage
    #PatientStage
)

# Registering all models in the admin interface
admin.site.register(Patient)
admin.site.register(PatientHistory)
admin.site.register(NewRecommendationsStage)
admin.site.register(FollowUpStage)
admin.site.register(ClinicalInterventionStage)
admin.site.register(QuotationPhaseStage)
admin.site.register(ReadyToScheduleStage)
admin.site.register(PreAdmissionPrepStage)
admin.site.register(PostponedAdmissionsStage)
admin.site.register(ClinicalStage)
admin.site.register(InitialTransitionStage)
admin.site.register(FinalTransitionStage)
admin.site.register(ClosedStage)
#admin.site.register(CohortAStage)
#admin.site.register(PatientStage)
