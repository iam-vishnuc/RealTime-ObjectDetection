
from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse, JsonResponse, FileResponse
from PIL import Image
from django.urls import reverse
from ultralytics import YOLO
import cv2
import time
import os
import json
from .forms import DatasetUploadForm
from .models import Dataset,Register
import zipfile
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import DetectionResultSerializer
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

model_choices = {
    'yolov8s': 'yolov8s.pt',
    'yolov8m': 'yolov8m.pt',  
    'yolov9s': 'yolov9s.pt',    
    'yolov10s': 'yolov10s.pt',    
    'yolov10n': 'yolov10n.pt',        
}
current_model = YOLO(model_choices['yolov8s']) 
default_confidence = 0.5

# Paths for saving processed images and reports
PROCESSED_DIR = 'media/processed/'
REPORTS_DIR = 'media/reports/'


os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

@login_required
def home(request):
    return render(request, 'base.html')

@login_required
def upload(request):
    return render(request, 'upload.html')

@login_required
def update_settings(request):
    global current_model, default_confidence
    if request.method == 'POST':
        action = request.POST.get('action') 

       
        if action == 'switch_model':
            selected_model = request.POST.get('model')
            if selected_model in model_choices:
                current_model = YOLO(model_choices[selected_model])
                message = f"Model switched to {selected_model}"

       
        elif action == 'update_confidence':
            confidence = float(request.POST.get('confidence', default_confidence))
            default_confidence = confidence
            message = "Confidence threshold updated successfully"
        if message:
            return render(request, 'settings.html', {'message': message})

    return render(request, 'settings.html', {'message': 'Invalid request'})

@login_required
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES['image']
        try:
            image = Image.open(image_file)
            results = current_model(image)

            detections = []
            label_count = {}
            for r in results[0].boxes:
                conf = float(r.conf[0])
                if conf >= default_confidence:
                    cls = int(r.cls[0])
                    name = current_model.names[cls]
                    label_count[name] = label_count.get(name, 0) + 1
                    detections.append({
                        "x1": int(r.xyxy[0][0]),
                        "y1": int(r.xyxy[0][1]),
                        "x2": int(r.xyxy[0][2]),
                        "y2": int(r.xyxy[0][3]),
                        "confidence": conf,
                        "class": cls,
                        "name": name
                    })

            
            processed_image_path = os.path.join(PROCESSED_DIR, f"processed_{image_file.name}")
            annotated_image = results[0].plot()
            annotated_image_pil = Image.fromarray(annotated_image)
            annotated_image_pil.save(processed_image_path)

           
            report_path = os.path.join(REPORTS_DIR, f"report_{image_file.name}.json")
            with open(report_path, 'w') as report_file:
                json.dump(detections, report_file)

            return render(request, 'upload.html', {
                'detections': detections,
                'label_count': label_count,
                'processed_image': processed_image_path,
                'report': report_path
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return render(request, 'upload.html')




# Define directories for saving uploaded and processed videos
UPLOAD_DIR = 'media/videos'
PROCESSED_DIR = 'media/processed_videos'
REPORTS_DIR = 'media/reports'

# Create directories if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

@login_required
def upload_video(request):
    if request.method == 'POST' and request.FILES.get('video'):
        video_file = request.FILES['video']
        try:
            # Save the uploaded video
            video_path = os.path.join(UPLOAD_DIR, video_file.name)
            with open(video_path, 'wb+') as destination:
                for chunk in video_file.chunks():
                    destination.write(chunk)

            # Use the currently selected model
            global current_model  # Access the globally defined current_model
            model = current_model  # Use the current model for object detection

            # Open the video file
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return JsonResponse({'error': 'Unable to open video file'}, status=400)

            # Get video properties
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))

            # Define the codec and create a VideoWriter object to save the processed video
            processed_video_path = os.path.join(PROCESSED_DIR, f"processed_{video_file.name}")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for .mp4 files
            out = cv2.VideoWriter(processed_video_path, fourcc, fps, (frame_width, frame_height))

            detections = []  # Store detection results for the report

            # Process each frame of the video
            frame_count = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Perform object detection on the frame
                results = model(frame)

                # Draw bounding boxes and labels on the frame
                for r in results[0].boxes:
                    conf = float(r.conf[0])
                    if conf >= default_confidence:
                        cls = int(r.cls[0])
                        name = model.names[cls]  # Use the model's class names
                        x1, y1, x2, y2 = map(int, r.xyxy[0])

                        # Draw bounding box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                        # Add label and confidence
                        label = f"{name} {conf:.2f}"
                        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                        # Store detection results
                        detections.append({
                            "frame": frame_count,
                            "name": name,
                            "confidence": conf,
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                        })

                # Write the processed frame to the output video
                out.write(frame)
                frame_count += 1

            # Release the video capture and writer objects
            cap.release()
            out.release()

            # Generate a report
            report_path = os.path.join(REPORTS_DIR, f"report_{video_file.name}.json")
            with open(report_path, 'w') as report_file:
                json.dump({
                    "status": "success",
                    "video": video_file.name,
                    "detections": detections
                }, report_file)

            return render(request, 'upload.html', {
                'video_path': video_path,
                'processed_video_path': processed_video_path,
                'report_path': report_path
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return render(request, 'upload.html')




@login_required
def stream_video(request):
    cap = cv2.VideoCapture(0)

    def generate_frames():
        try:
            while True:
                start_time = time.time()
                success, frame = cap.read()
                if not success:
                    break

                results = current_model(frame)
                for r in results[0].boxes:
                    conf = float(r.conf[0])
                    if conf >= default_confidence:
                        x1, y1, x2, y2 = map(int, r.xyxy[0])
                        cls = int(r.cls[0])
                        label = current_model.names[cls]

                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)


                _, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        finally:
            cap.release()

    return StreamingHttpResponse(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')

def live_stream(request):
    context = {
        'video_stream_url': reverse('stream_video'),
    }
    return render(request, 'streamvideo.html', context)

@login_required
def download_file(request, file_type, filename):
    directory = PROCESSED_DIR if file_type == 'image' else REPORTS_DIR
    file_path = os.path.join(directory, filename)

    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    else:
        return JsonResponse({'error': 'File not found'}, status=404)


@login_required
def settings_page(request):
    return render(request, 'settings.html', {
        'models': model_choices.keys(),
        'default_confidence': default_confidence
    })



# Path to store extracted datasets
EXTRACTED_DATASETS_DIR = 'media/extracted_datasets/'
os.makedirs(EXTRACTED_DATASETS_DIR, exist_ok=True)

@login_required
def upload_dataset(request):
    if request.method == 'POST':
        form = DatasetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dataset = form.save()

           
            with zipfile.ZipFile(dataset.zip_file.path, 'r') as zip_ref:
                extract_path = os.path.join(EXTRACTED_DATASETS_DIR, dataset.name)
                os.makedirs(extract_path, exist_ok=True)
                zip_ref.extractall(extract_path)

            return redirect('train_model') 
    else:
        form = DatasetUploadForm()

    return render(request, 'upload_dataset.html', {'form': form})


@login_required
def train_model(request):
    if request.method == 'POST':
        dataset_name = request.POST.get('dataset_name')
        dataset_path = os.path.join(EXTRACTED_DATASETS_DIR, dataset_name)

        
        try:
            from ultralytics import YOLO

            model = YOLO('yolov8s.pt') 
            model.train(data=f'{dataset_path}/data.yaml', epochs=10, imgsz=640)

            return JsonResponse({'message': f'Model trained successfully using {dataset_name} dataset'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    datasets = os.listdir(EXTRACTED_DATASETS_DIR)
    return render(request, 'train_model.html', {'datasets': datasets})




def user_register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use!")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, "Registration successful! Please log in.")
        return redirect('user_login')
    return render(request, 'register.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('/')
        else:
            messages.error(request, "Invalid credentials! Please try again.")
            return redirect('user_login')
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'you have been logged out')
    return redirect('user_login')



#api

class ObjectDetectionAPI(APIView):
    def post(self, request):
        if 'image' not in request.FILES:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES['image']
        image = Image.open(image_file)
        results = current_model(image)

        detections = []
        for r in results[0].boxes:
            conf = float(r.conf[0])
            if conf >= default_confidence:
                cls = int(r.cls[0])
                name = current_model.names[cls]
                detections.append({
                    "name": name,
                    "confidence": conf,
                    "x1": int(r.xyxy[0][0]),
                    "y1": int(r.xyxy[0][1]),
                    "x2": int(r.xyxy[0][2]),
                    "y2": int(r.xyxy[0][3]),
                })

        serializer = DetectionResultSerializer(detections, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SwitchModelAPI(APIView):
    def post(self, request):
        selected_model = request.data.get('model')
        if selected_model not in model_choices:
            return Response({"error": "Invalid model selected"}, status=status.HTTP_400_BAD_REQUEST)

        global current_model
        current_model = YOLO(model_choices[selected_model])
        return Response({"message": f"Model switched to {selected_model}"}, status=status.HTTP_200_OK)

class ConfidenceThresholdAPI(APIView):
    def post(self, request):
        confidence = request.data.get('confidence')
        if not (0.1 <= confidence <= 1.0):
            return Response({"error": "Confidence must be between 0.1 and 1.0"}, status=status.HTTP_400_BAD_REQUEST)

        global default_confidence
        default_confidence = confidence
        return Response({"message": "Confidence threshold updated successfully"}, status=status.HTTP_200_OK)