from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Patient, PatientHistory
from .serializers import PatientSerializer, PatientHistorySerializer

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
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

        previous_cohort = patient.current_cohort
        previous_sub_stage = patient.current_sub_stage

        for transition in state_transitions['state_transitions']:
            if (patient.current_sub_stage == transition['current_sub_stage'] and 
                patient.current_cohort == transition['current_cohort']):
                
                conditions_met = True

                # Check actions
                for action in transition['conditions'].get('actions', []):
                    patient_value = getattr(patient, action['condition'], None)
                    if patient_value is None:
                        conditions_met = False
                        break

                    operator = action['operator']
                    value = action['value']
                    # Try converting value to integer if it's supposed to be numeric
                    try:
                        if isinstance(value, str) and value.isdigit():
                            value = int(value)
                    except ValueError:
                        return Response({"error": "Invalid value for condition"}, status=status.HTTP_400_BAD_REQUEST)

                    # Compare patient value with the specified condition
                    if operator == ">=" and not (patient_value >= value):
                        conditions_met = False
                        break
                    elif operator == ">" and not (patient_value > value):
                        conditions_met = False
                        break
                    elif operator == "<=" and not (patient_value <= value):
                        conditions_met = False
                        break
                    elif operator == "<" and not (patient_value < value):
                        conditions_met = False
                        break

                # Check dispositions
                for disposition in transition['conditions'].get('dispositions', []):
                    patient_value = getattr(patient, disposition['condition'], None)
                    if patient_value is None or patient_value != disposition['value']:
                        conditions_met = False
                        break

                    # Handle sub-condition if present
                    if 'sub_condition' in disposition:
                        sub_condition = disposition['sub_condition']
                        sub_patient_value = getattr(patient, sub_condition['condition'], None)
                        if sub_patient_value is None or sub_patient_value != sub_condition['value']:
                            conditions_met = False
                            break

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
                    return Response({"message": "Patient transitioned successfully", "patient_id": patient.id}, status=status.HTTP_200_OK)

        return Response({"message": "No transition applied"}, status=status.HTTP_400_BAD_REQUEST)

    def get_history(self, request, patient_id):
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve the patient's history
        history_entries = PatientHistory.objects.filter(patient=patient)
        serializer = PatientHistorySerializer(history_entries, many=True)

        return Response({"patient_id": patient.id, "history": serializer.data}, status=status.HTTP_200_OK)