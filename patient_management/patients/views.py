from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import (
    Patient, PatientHistory, NewRecommendationsStage, FollowUpStage,
    ClinicalInterventionStage, QuotationPhaseStage, ReadyToScheduleStage,
    PreAdmissionPrepStage, PostponedAdmissionsStage, ClinicalStage,
    InitialTransitionStage, FinalTransitionStage, ClosedStage
)
from .serializers import PatientSerializer, PatientHistorySerializer
import logging

logger = logging.getLogger(__name__)

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
            try:
                patient = serializer.save()
                logger.info(f"Patient admitted successfully with ID: {patient.id}")
                return Response({"message": "Patient admitted successfully", "patient_id": patient.id}, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Failed to admit patient: {e}")
                return Response({"error": "Failed to admit patient"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.warning(f"Patient admission failed with errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def transition(self, request, patient_id):
        try:
            patient = Patient.objects.get(id=patient_id)
            logger.info(f"Transition initiated for patient ID: {patient_id}")
        except Patient.DoesNotExist:
            logger.error(f"Patient with ID {patient_id} not found")
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

        previous_cohort = patient.current_cohort
        previous_sub_stage = patient.current_sub_stage

        for transition in state_transitions['state_transitions']:
            if (patient.current_sub_stage == transition['current_sub_stage'] and 
                patient.current_cohort == transition['current_cohort']):
                
                logger.info(f"Evaluating transition for cohort: {patient.current_cohort}, sub-stage: {patient.current_sub_stage}")

                if self._check_conditions(patient, transition['conditions']):
                    patient.previous_cohort = previous_cohort
                    patient.previous_sub_stage = previous_sub_stage
                    patient.current_cohort = transition['next_cohort']
                    patient.current_sub_stage = transition['next_sub_cohort']
                    
                    try:
                        patient.save()
                        logger.info(f"Patient cohort and sub-stage updated to: {patient.current_cohort}, {patient.current_sub_stage}")
                    except Exception as e:
                        logger.error(f"Failed to save patient data: {e}")
                        return Response({"error": "Failed to save patient data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    try:
                        PatientHistory.objects.create(
                            patient=patient,
                            previous_cohort=previous_cohort,
                            previous_sub_stage=previous_sub_stage,
                            next_cohort=transition['next_cohort'],
                            next_sub_stage=transition['next_sub_cohort'],
                        )
                        logger.info("Transition history saved.")
                    except Exception as e:
                        logger.error(f"Failed to save transition history: {e}")
                        return Response({"error": "Failed to save transition history"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    logger.info(f"Calling _move_to_stage for patient ID {patient.id} with cohort {patient.current_cohort}")
                    self._move_to_stage(patient)
                    return Response({"message": "Patient transitioned successfully", "patient_id": patient.id}, status=status.HTTP_200_OK)

        logger.warning("No transition applied.")
        return Response({"message": "No transition applied"}, status=status.HTTP_400_BAD_REQUEST)

    def _check_conditions(self, patient, conditions):
        logger.info("Checking conditions for transition.")
        for action in conditions.get('actions', []):
            if not self._evaluate_condition(patient, action):
                logger.info(f"Action condition not met: {action}")
                return False
        for disposition in conditions.get('dispositions', []):
            if not self._evaluate_condition(patient, disposition):
                logger.info(f"Disposition condition not met: {disposition}")
                return False
        logger.info("All conditions met for transition.")
        return True

    def _evaluate_condition(self, patient, condition):
        patient_value = getattr(patient, condition['condition'], None)
        if patient_value is None:
            logger.warning(f"Condition {condition['condition']} not found on patient.")
            return False

        operator = condition.get('operator')
        value = condition['value']

        if operator == ">=":
            return patient_value >= value
        elif operator == ">":
            return patient_value > value
        elif operator == "<=":
            return patient_value <= value
        elif operator == "<":
            return patient_value < value
        return patient_value == value
    
    def _move_to_stage(self, patient):
        logger.info(f"Entered _move_to_stage function for patient ID: {patient.id}.")
        stage_classes = {
            "Follow-up": FollowUpStage,
            "Clinical Intervention": ClinicalInterventionStage,
            "Quotation Phase": QuotationPhaseStage,
            "Ready to Schedule": ReadyToScheduleStage,
            "Pre-Admission Prep": PreAdmissionPrepStage,
            "Postponed Admissions": PostponedAdmissionsStage,
            "Clinical Stage": ClinicalStage,
            "Initial Transition": InitialTransitionStage,
            "Final Transition": FinalTransitionStage,
            "Closed": ClosedStage
        }

        try:
            stage_class = stage_classes.get(patient.current_cohort)
            if not stage_class:
                logger.error(f"Stage class not found for cohort: {patient.current_cohort}")
                return Response(
                    {"error": f"Stage class not found for cohort: {patient.current_cohort}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            logger.info(f"Attempting to create a new stage for patient ID {patient.id} in cohort {patient.current_cohort}")
            
            stage_instance = stage_class.objects.create(patient=patient)
            
            # Verification log to confirm instance creation
            logger.info(f"New stage instance created for patient ID {patient.id} in cohort {patient.current_cohort}")

            # Double-check stage creation in the database
            saved_stage = stage_class.objects.filter(patient=patient).latest('id')
            if saved_stage != stage_instance:
                logger.error(f"Stage creation verification failed for patient ID {patient.id}.")
                return Response(
                    {"error": "Stage creation verification failed"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            logger.info(f"Patient moved to stage {patient.current_cohort} successfully.")
        
        except Exception as e:
            logger.error(f"Failed to move patient to stage: {e}")
            return Response(
                {"error": f"Failed to move patient to stage: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_history(self, request, patient_id):
        try:
            patient = Patient.objects.get(id=patient_id)
            logger.info(f"Retrieving history for patient ID: {patient_id}")
        except Patient.DoesNotExist:
            logger.error(f"Patient with ID {patient_id} not found")
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

        history_entries = PatientHistory.objects.filter(patient=patient)
        serializer = PatientHistorySerializer(history_entries, many=True)
        return Response({"patient_id": patient.id, "history": serializer.data}, status=status.HTTP_200_OK)
