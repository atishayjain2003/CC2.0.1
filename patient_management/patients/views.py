from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Patient, PatientHistory
from .serializers import PatientSerializer, PatientHistorySerializer
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import (
    Patient, PatientHistory, NewRecommendationsStage, FollowUpStage,
    ClinicalInterventionStage, QuotationPhaseStage, ReadyToScheduleStage,
    PreAdmissionPrepStage, PostponedAdmissionsStage, ClinicalStage,
    InitialTransitionStage, FinalTransitionStage, ClosedStage
)
from .serializers import PatientSerializer, PatientHistorySerializer
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Patient, PatientHistory, FollowUpStage, ClinicalInterventionStage, QuotationPhaseStage, ReadyToScheduleStage, PreAdmissionPrepStage, PostponedAdmissionsStage, ClinicalStage, InitialTransitionStage, FinalTransitionStage, ClosedStage
from .serializers import PatientSerializer, PatientHistorySerializer
from django.shortcuts import get_object_or_404

# Load the state transition JSON structure
state_transitions = {
    "state_transitions": [
        {
            "current_sub_stage": "A1",
            "current_cohort": "New Recommendations",
            "conditions": {
                "actions": [
                    {
                        "condition": "days_since_follow_up",
                        "operator": ">=",
                        "value": 1
                    }
                ],
                "dispositions": [
                    {
                        "condition": "clinical_intervention_required",
                        "value": True
                    },
                    {
                        "condition": "quotation_phase_required",
                        "value": True
                    },
                    {
                        "condition": "patient_ready",
                        "value": True
                    }
                ]
            },
            "next_cohort": "A",
            "next_sub_cohort": "Follow-up"
        },
        {
            "current_sub_stage": "A2",
            "current_cohort": "Clinical Intervention",
            "conditions": {
                "actions": [
                    {
                        "condition": "days_since_last_contact",
                        "operator": ">",
                        "value": "Y"
                    }
                ],
                "dispositions": [
                    {
                        "condition": "clinical_intervention_completed",
                        "value": True
                    },
                    {
                        "condition": "quotation_phase_required",
                        "value": False
                    }
                ]
            },
            "next_cohort": "C",
            "next_sub_cohort": "Clinical Stage"
        },
        {
            "current_sub_stage": "A3",
            "current_cohort": "Quotation Phase",
            "conditions": {
                "dispositions": [
                    {
                        "condition": "quotation_accepted",
                        "value": True
                    },
                    {
                        "condition": "days_since_last_contact",
                        "operator": ">",
                        "value": "Y"
                    }
                ]
            },
            "next_cohort": "A4",
            "next_sub_cohort": "Ready to Schedule"
        },
        {
            "current_sub_stage": "A4",
            "current_cohort": "Ready to Schedule",
            "conditions": {
                "dispositions": [
                    {
                        "condition": "scheduled_admission",
                        "value": True
                    }
                ]
            },
            "next_cohort": "B",
            "next_sub_cohort": "Pre-Admission Prep"
        },
        {
            "current_sub_stage": "B1",
            "current_cohort": "Pre-Admission Prep",
            "conditions": {
                "actions": [
                    {
                        "condition": "days_until_admission",
                        "operator": "<=",
                        "value": "Z"
                    }
                ],
                "dispositions": [
                    {
                        "condition": "admission_status",
                        "value": "Postponed"
                    }
                ]
            },
            "next_cohort": "C",
            "next_sub_cohort": "Postponed Admissions"
        },
        {
            "current_sub_stage": "B2",
            "current_cohort": "Admission Soon",
            "conditions": {
                "dispositions": [
                    {
                        "condition": "admission_status",
                        "value": "Cancelled"
                    }
                ]
            },
            "next_cohort": "C",
            "next_sub_cohort": "Postponed Admissions"
        },
        {
            "current_sub_stage": "C1",
            "current_cohort": "Postponed Admissions",
            "conditions": {
                "dispositions": [
                    {
                        "condition": "scheduled_date_in_past",
                        "value": True,
                        "sub_condition": {
                            "condition": "admission_completed",
                            "value": False
                        }
                    }
                ]
            },
            "next_cohort": "D",
            "next_sub_cohort": "Clinical Stage"
        },
        {
            "current_sub_stage": "C2",
            "current_cohort": "Clinical Stage",
            "conditions": {
                "dispositions": [
                    {
                        "condition": "clinical_intervention_completed",
                        "value": True
                    }
                ]
            },
            "next_cohort": "E",
            "next_sub_cohort": "Initial Transition"
        },
        {
            "current_sub_stage": "E1",
            "current_cohort": "Initial Transition",
            "conditions": {
                "dispositions": [
                    {
                        "condition": "lead_management_ends",
                        "value": True
                    }
                ]
            },
            "next_cohort": "E",
            "next_sub_cohort": "Move to previous"
        },
        {
            "current_sub_stage": "E2",
            "current_cohort": "Final Transition",
            "conditions": {
                "dispositions": [
                    {
                        "condition": "follow_up_attempts",
                        "operator": ">",
                        "value": "Final"
                    },
                    {
                        "condition": "final_response_received",
                        "value": True
                    }
                ]
            },
            "next_cohort": "End",
            "next_sub_cohort": "Closed"
        }
    ]
}

class PatientViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = PatientSerializer(data=request.data)
        if serializer.is_valid():
            patient = serializer.save()
            return Response({"message": "Patient admitted successfully", "patient_id": patient.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def transition(self, request, patient_id):
        """
        Triggers a state transition for the patient based on conditions and moves data to the appropriate stage table.
        """
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

        previous_cohort = patient.current_cohort
        previous_sub_stage = patient.current_sub_stage

        # Iterate over state transitions and apply conditions
        for transition in state_transitions['state_transitions']:
            if (patient.current_sub_stage == transition['current_sub_stage'] and 
                patient.current_cohort == transition['current_cohort']):

                conditions_met = self._check_conditions(patient, transition['conditions'])

                if conditions_met:
                    # Update patient's cohort and sub-stage
                    patient.previous_cohort = previous_cohort
                    patient.previous_sub_stage = previous_sub_stage
                    patient.current_cohort = transition['next_cohort']
                    patient.current_sub_stage = transition['next_sub_cohort']

                    # Save the patient and log the history
                    patient.save()
                    PatientHistory.objects.create(
                        patient=patient,
                        previous_cohort=previous_cohort,
                        previous_sub_stage=previous_sub_stage,
                        next_cohort=transition['next_cohort'],
                        next_sub_stage=transition['next_sub_cohort'],
                    )

                    # Move to the appropriate stage
                    self._move_to_stage(patient)

                    return Response({"message": "Patient transitioned successfully", "patient_id": patient.id}, status=status.HTTP_200_OK)

        return Response({"message": "No transition applied"}, status=status.HTTP_400_BAD_REQUEST)

    def _check_conditions(self, patient, conditions):
        """
        Checks if the conditions are met for the state transition.
        """
        conditions_met = True

        # Check actions (e.g., "days_since_follow_up >= 1")
        for action in conditions.get('actions', []):
            if not self._evaluate_condition(patient, action):
                conditions_met = False
                break

        # Check dispositions (e.g., "clinical_intervention_required == True")
        for disposition in conditions.get('dispositions', []):
            if not self._evaluate_condition(patient, disposition):
                conditions_met = False
                break

        return conditions_met

    def _evaluate_condition(self, patient, condition):
        """
        Evaluates a single condition for the patient.
        """
        patient_value = getattr(patient, condition['condition'], None)
        if patient_value is None:
            return False

        # Convert value to integer if it's a digit-based condition
        value = condition['value']
        if isinstance(value, str) and value.isdigit():
            value = int(value)

        operator = condition.get('operator', None)

        # Handle comparisons based on the operator
        if operator == ">=":
            return patient_value >= value
        elif operator == ">":
            return patient_value > value
        elif operator == "<=":
            return patient_value <= value
        elif operator == "<":
            return patient_value < value
        elif operator is None:
            return patient_value == value

        return False

    def _move_to_stage(self, patient):
        """
        Moves patient data to the appropriate stage table and clears data from other stages.
        """
        # Clear patient data from all stage tables first
        FollowUpStage.objects.filter(patient=patient).delete()
        ClinicalInterventionStage.objects.filter(patient=patient).delete()
        QuotationPhaseStage.objects.filter(patient=patient).delete()
        ReadyToScheduleStage.objects.filter(patient=patient).delete()
        PreAdmissionPrepStage.objects.filter(patient=patient).delete()
        PostponedAdmissionsStage.objects.filter(patient=patient).delete()
        ClinicalStage.objects.filter(patient=patient).delete()
        InitialTransitionStage.objects.filter(patient=patient).delete()
        FinalTransitionStage.objects.filter(patient=patient).delete()
        ClosedStage.objects.filter(patient=patient).delete()

        # Move data to the appropriate table based on the new cohort and sub-stage
        if patient.current_cohort == "FollowUp":
            FollowUpStage.objects.create(patient=patient, days_since_follow_up=patient.days_since_follow_up)
        elif patient.current_cohort == "ClinicalIntervention":
            ClinicalInterventionStage.objects.create(patient=patient, clinical_intervention_completed=patient.clinical_intervention_completed)
        elif patient.current_cohort == "QuotationPhase":
            QuotationPhaseStage.objects.create(patient=patient, quotation_accepted=patient.quotation_accepted)
        elif patient.current_cohort == "ReadyToSchedule":
            ReadyToScheduleStage.objects.create(patient=patient, scheduled_admission=patient.scheduled_admission)
        elif patient.current_cohort == "PreAdmissionPrep":
            PreAdmissionPrepStage.objects.create(patient=patient, days_until_admission=patient.days_until_admission, admission_status=patient.admission_status)
        elif patient.current_cohort == "PostponedAdmissions":
            PostponedAdmissionsStage.objects.create(patient=patient, scheduled_date_in_past=patient.scheduled_date_in_past)
        elif patient.current_cohort == "Clinical":
            ClinicalStage.objects.create(patient=patient, clinical_intervention_completed=patient.clinical_intervention_completed)
        elif patient.current_cohort == "InitialTransition":
            InitialTransitionStage.objects.create(patient=patient, lead_management_ends=patient.lead_management_ends)
        elif patient.current_cohort == "FinalTransition":
            FinalTransitionStage.objects.create(patient=patient, follow_up_attempts=patient.follow_up_attempts)
        elif patient.current_cohort == "Closed":
            ClosedStage.objects.create(patient=patient)

    def get_history(self, request, patient_id):
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve the patient's history
        history_entries = PatientHistory.objects.filter(patient=patient)
        serializer = PatientHistorySerializer(history_entries, many=True)

        return Response({"patient_id": patient.id, "history": serializer.data}, status=status.HTTP_200_OK)  