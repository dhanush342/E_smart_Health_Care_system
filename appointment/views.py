from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rl_scheduler.pipeline import MultiStageRLSchedulerPipeline, run_comprehensive_benchmark
from rl_scheduler.data_types import PatientProfile

pipeline_instance = MultiStageRLSchedulerPipeline()

@csrf_exempt
def rl_benchmark_view(request):
    """
    Runs comprehensive comparison between Multi-Stage RL and baseline algorithms
    (FCFS, Fixed-Slot, Heuristic Priority) across low, medium, and high demand scenarios.
    """
    episodes = request.GET.get('episodes', 10)
    try:
        episodes = int(episodes)
    except ValueError:
        episodes = 10

    benchmark_data = run_comprehensive_benchmark(num_train_episodes=episodes)

    # Format result as JSON
    json_response = {}
    for scenario, schedulers in benchmark_data.items():
        json_response[scenario] = {}
        for name, m in schedulers.items():
            json_response[scenario][name] = {
                "total_patients": m.total_patients,
                "completed_patients": m.completed_patients,
                "cancelled_patients": m.cancelled_patients,
                "avg_wait_time": round(m.avg_wait_time, 2),
                "doctor_idle_time": round(m.doctor_idle_time, 2),
                "priority_fairness_score": round(m.priority_fairness_score, 2),
                "throughput_per_hour": round(m.throughput, 2)
            }

    return JsonResponse({
        "status": "success",
        "benchmark_results": json_response
    })

@csrf_exempt
def rl_optimize_schedule_view(request):
    """
    Dynamically processes a list of incoming patient profiles through the 3-Stage RL system:
    Triage (DQN) -> Slot Scheduling (Double DQN) -> Live Queue Execution (PPO).
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            patient_list_data = data.get('patients', [])
        except Exception:
            patient_list_data = []

        patient_profiles = []
        for i, pdata in enumerate(patient_list_data):
            patient_profiles.append(PatientProfile(
                patient_id=pdata.get('patient_id', f"PAT_{i}"),
                severity=int(pdata.get('severity', 3)),
                condition=pdata.get('condition', 'General Consult'),
                target_department=int(pdata.get('target_department', 0)),
                base_consultation_time=float(pdata.get('base_consultation_time', 15.0)),
                cancellation_prob=float(pdata.get('cancellation_prob', 0.1)),
                is_emergency=bool(pdata.get('is_emergency', False)),
                arrival_time=float(pdata.get('arrival_time', 0.0))
            ))

        if not patient_profiles:
            return JsonResponse({"status": "error", "message": "No valid patient profiles provided."}, status=400)

        metrics, completed_patients = pipeline_instance.run_multi_stage_execution(patient_profiles)

        return JsonResponse({
            "status": "success",
            "summary": {
                "total_patients": metrics.total_patients,
                "completed_patients": metrics.completed_patients,
                "avg_wait_time": round(metrics.avg_wait_time, 2),
                "doctor_idle_time": round(metrics.doctor_idle_time, 2),
                "priority_fairness_score": round(metrics.priority_fairness_score, 2)
            },
            "completed_schedule": [
                {
                    "patient_id": p.patient_id,
                    "severity": p.severity,
                    "assigned_dept": p.target_department,
                    "scheduled_slot": p.scheduled_slot,
                    "start_time": round(p.start_service_time, 2) if p.start_service_time else None,
                    "completion_time": round(p.completion_time, 2) if p.completion_time else None,
                    "wait_time": round(p.calculate_wait_time(), 2)
                } for p in completed_patients
            ]
        })

    return JsonResponse({"status": "error", "message": "POST method required."}, status=405)
