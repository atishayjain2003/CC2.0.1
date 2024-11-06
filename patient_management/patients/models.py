from django.db import models

class Patient(models.Model):
    # Patient-related fields
    name = models.CharField(max_length=100)
    current_cohort = models.CharField(max_length=50)
    current_sub_stage = models.CharField(max_length=50)
    previous_cohort = models.CharField(max_length=50, null=True, blank=True)
    previous_sub_stage = models.CharField(max_length=50, null=True, blank=True)
    
    # Time and flag-related fields for conditions
    days_since_follow_up = models.IntegerField(default=0)
    days_since_last_contact = models.IntegerField(default=0)
    days_until_admission = models.IntegerField(default=0)  # For days-based conditions
    
    # Status flags
    clinical_intervention_required = models.BooleanField(default=False)
    quotation_phase_required = models.BooleanField(default=False)
    patient_ready = models.BooleanField(default=False)
    clinical_intervention_completed = models.BooleanField(default=False)
    quotation_accepted = models.BooleanField(default=False)
    scheduled_admission = models.BooleanField(default=False)
    scheduled_date_in_past = models.BooleanField(default=False)
    admission_completed = models.BooleanField(default=False)
    lead_management_ends = models.BooleanField(default=False)
    final_response_received = models.BooleanField(default=False)
    admission_status = models.CharField(max_length=50, choices=[('Postponed', 'Postponed'), ('Cancelled', 'Cancelled')], default='Postponed')
    follow_up_attempts = models.CharField(max_length=50, default='None')

    def __str__(self):
        return self.name


class PatientHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    previous_cohort = models.CharField(max_length=50)
    previous_sub_stage = models.CharField(max_length=50)
    next_cohort = models.CharField(max_length=50)
    next_sub_stage = models.CharField(max_length=50)
    transition_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transition of {self.patient.name} from {self.previous_cohort} ({self.previous_sub_stage}) to {self.next_cohort} ({self.next_sub_stage})"


# Base model for all stage data
class PatientStage(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True

# Models for each cohort and substage with specific fields

class NewRecommendationsStage(PatientStage):
    days_since_follow_up = models.IntegerField(default=0)
    clinical_intervention_required = models.BooleanField(default=False)
    quotation_phase_required = models.BooleanField(default=False)
    patient_ready = models.BooleanField(default=False)


class FollowUpStage(PatientStage):
    days_since_follow_up = models.IntegerField(default=0)
    clinical_intervention_completed = models.BooleanField(default=False)
    quotation_phase_required = models.BooleanField(default=False)


class ClinicalInterventionStage(PatientStage):
    clinical_intervention_completed = models.BooleanField(default=False)
    quotation_accepted = models.BooleanField(default=False)


class QuotationPhaseStage(PatientStage):
    quotation_accepted = models.BooleanField(default=False)
    days_since_last_contact = models.IntegerField(default=0)


class ReadyToScheduleStage(PatientStage):
    scheduled_admission = models.BooleanField(default=False)


class PreAdmissionPrepStage(PatientStage):
    days_until_admission = models.IntegerField(default=0)
    admission_status = models.CharField(max_length=50, choices=[('Postponed', 'Postponed'), ('Cancelled', 'Cancelled')], default='Postponed')


class PostponedAdmissionsStage(PatientStage):
    scheduled_date_in_past = models.BooleanField(default=False)
    admission_completed = models.BooleanField(default=False)


class ClinicalStage(PatientStage):
    clinical_intervention_completed = models.BooleanField(default=False)


class InitialTransitionStage(PatientStage):
    lead_management_ends = models.BooleanField(default=False)


class FinalTransitionStage(PatientStage):
    follow_up_attempts = models.CharField(max_length=50, default='None')
    final_response_received = models.BooleanField(default=False)


class ClosedStage(PatientStage):
    # Final closed stage
    pass
