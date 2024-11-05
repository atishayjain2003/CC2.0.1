from django.urls import path
from .views import PatientViewSet

# Defining individual views for each action in the PatientViewSet
create_patient_view = PatientViewSet.as_view({
    'post': 'create',
})

get_history_view = PatientViewSet.as_view({
    'get': 'get_history',
})

transition_view = PatientViewSet.as_view({
    'put': 'transition',
})

urlpatterns = [
    path('patients/', create_patient_view, name='patient-list'),  # Endpoint for creating a patient
    path('patients/<int:patient_id>/history/', get_history_view, name='patient-history'),  # Endpoint for retrieving patient history
    path('patients/<int:patient_id>/transition/', transition_view, name='patient-transition'),  # Endpoint for transitioning patient stages
]
