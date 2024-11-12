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
    admission_status = models.CharField(max_length=50, choices=[('Postponed', 'Postponed'), ('Cancelled', 'Cancelled'), ('Pending', 'Pending')], default='Postponed')
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
class CohortAStage(PatientStage):
    # Cohort A-specific fields, if any common field across stages
    #cohort_a_specific_field = models.CharField(max_length=100, null=True, blank=True)  # Example

    class Meta:
        abstract = True  # Make this model abstract as it's for subclassing
class CohortBStage(PatientStage):
    # Cohort A-specific fields, if any common field across stages
    #cohort_a_specific_field = models.CharField(max_length=100, null=True, blank=True)  # Example

    class Meta:
        abstract = True  # Make this model abstract as it's for subclassing
class CohortCStage(PatientStage):
    # Cohort A-specific fields, if any common field across stages
    #cohort_a_specific_field = models.CharField(max_length=100, null=True, blank=True)  # Example

    class Meta:
        abstract = True  # Make this model abstract as it's for subclassing
class CohortDStage(PatientStage):
    # Cohort A-specific fields, if any common field across stages
    #cohort_a_specific_field = models.CharField(max_length=100, null=True, blank=True)  # Example

    class Meta:
        abstract = True  # Make this model abstract as it's for subclassing
class CohortEStage(PatientStage):
    # Cohort A-specific fields, if any common field across stages
    #cohort_a_specific_field = models.CharField(max_length=100, null=True, blank=True)  # Example

    class Meta:
        abstract = True  # Make this model abstract as it's for subclassing
        

class NewRecommendationsStage(CohortAStage):
    days_since_follow_up = models.IntegerField(default=0)
    clinical_intervention_required = models.BooleanField(default=False)
    quotation_phase_required = models.BooleanField(default=False)
    patient_ready = models.BooleanField(default=False)


class FollowUpStage(CohortAStage):
    days_since_follow_up = models.IntegerField(default=0)
    clinical_intervention_completed = models.BooleanField(default=False)
    quotation_phase_required = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.patient.name}"


class ClinicalInterventionStage(CohortBStage):
    clinical_intervention_completed = models.BooleanField(default=False)
    quotation_accepted = models.BooleanField(default=False)


class QuotationPhaseStage(CohortBStage):
    quotation_accepted = models.BooleanField(default=False)
    days_since_last_contact = models.IntegerField(default=0)


class ReadyToScheduleStage(CohortCStage):
    scheduled_admission = models.BooleanField(default=False)


class PreAdmissionPrepStage(CohortCStage):
    days_until_admission = models.IntegerField(default=0)
    admission_status = models.CharField(max_length=50, choices=[('Postponed', 'Postponed'), ('Cancelled', 'Cancelled')], default='Postponed')


class PostponedAdmissionsStage(CohortCStage):
    scheduled_date_in_past = models.BooleanField(default=False)
    admission_completed = models.BooleanField(default=False)


class ClinicalStage(CohortDStage):
    clinical_intervention_completed = models.BooleanField(default=False)


class InitialTransitionStage(CohortEStage):
    lead_management_ends = models.BooleanField(default=False)


class FinalTransitionStage(CohortEStage):
    follow_up_attempts = models.CharField(max_length=50, default='None')
    final_response_received = models.BooleanField(default=False)


class ClosedStage(PatientStage):
    # Final closed stage
    pass
