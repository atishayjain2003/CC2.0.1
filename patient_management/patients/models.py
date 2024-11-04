from django.db import models

class Patient(models.Model):
    # Define your fields according to your requirements
    name = models.CharField(max_length=100)
    current_cohort = models.CharField(max_length=50)
    current_sub_stage = models.CharField(max_length=50)
    previous_cohort = models.CharField(max_length=50, null=True, blank=True)
    previous_sub_stage = models.CharField(max_length=50, null=True, blank=True)
    days_since_follow_up = models.IntegerField(default=0)
    days_since_last_contact = models.IntegerField(default=0)
    
    # Flags indicating status
    clinical_intervention_required = models.BooleanField(default=False)
    quotation_phase_required = models.BooleanField(default=False)
    patient_ready = models.BooleanField(default=False)
    clinical_intervention_completed = models.BooleanField(default=False)
    quotation_accepted = models.BooleanField(default=False)
    
    # Admission related fields
    admission_status = models.CharField(max_length=50, choices=[('Postponed', 'Postponed'), ('Cancelled', 'Cancelled')], default='Postponed')
    scheduled_admission = models.BooleanField(default=False)
    scheduled_date_in_past = models.BooleanField(default=False)
    admission_completed = models.BooleanField(default=False)
    
    # Follow-up management
    lead_management_ends = models.BooleanField(default=False)
    final_response_received = models.BooleanField(default=False)
    follow_up_attempts = models.CharField(max_length=50, default='None')  # Provide a default value

    def __str__(self):
        return self.name  # Add a string representation for easy identification

class PatientHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    previous_cohort = models.CharField(max_length=50)
    previous_sub_stage = models.CharField(max_length=50)
    next_cohort = models.CharField(max_length=50)
    next_sub_stage = models.CharField(max_length=50)
    transition_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transition of {self.patient.name} from {self.previous_cohort} ({self.previous_sub_stage}) to {self.next_cohort} ({self.next_sub_stage})"
