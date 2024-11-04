from django.urls import path
from .views import PatientViewSet

patient_viewset = PatientViewSet.as_view({
    'post': 'create',
    'get': 'get_history',  # Correctly mapping GET to history retrieval
    'put': 'transition',    # Transition method for PUT requests
})

urlpatterns = [
    path('api/patients/', patient_viewset, name='patient-list'),
    path('api/patients/<int:patient_id>/history/', patient_viewset, name='patient-history'),
    path('api/patients/<int:patient_id>/transition/', patient_viewset, name='patient-transition'),
]
