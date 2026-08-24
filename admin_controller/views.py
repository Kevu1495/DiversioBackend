import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from core.csv_parser import parse_csv

logger = logging.getLogger(__name__)


@require_GET
def health(request):
    return JsonResponse({
        "status": "ok",
    })

@require_POST
@csrf_exempt
def csv_parser(request):
    csv_file = request.FILES.get("file")
    logger.info("Received CSV parsing request.")
    if csv_file is None:
        logger.warning("Parsing failed: No file provided in request.")
        return JsonResponse({"status": "error", "error": "CSV file is required"}, status=400)

    if csv_file.size == 0:
        logger.warning(f"Parsing failed: File '{csv_file.name}' is empty.")
        return JsonResponse({"status": "error", "error": "CSV file is empty"}, status=400)

    if not csv_file.name.lower().endswith(".csv"):
        logger.warning(f"Parsing failed: Invalid file extension for '{csv_file.name}'.")
        return JsonResponse({"status": "error", "error": "Only CSV files are allowed"}, status=400)

    try:
        logger.info(f"Starting parsing for file: {csv_file.name} ({csv_file.size} bytes)")

        result = parse_csv(csv_file)
        logger.info(f"Successfully processed CSV. Total rows: {result.get('total_rows')}")

        # 3. Return the result immediately
        # We use {**result, "status": "ok"} to merge the status into the result dictionary
        return JsonResponse({
            "status": "ok",
            **result
        })

    except ValueError as exc:
        logger.warning(f"Parsing failed: {str(exc)}")
        return JsonResponse({"status": "error", "error": str(exc)}, status=400)

    except Exception:
        logger.exception("Unexpected error while processing CSV")
        return JsonResponse({"status": "error", "error": "Failed to process CSV file"}, status=500)