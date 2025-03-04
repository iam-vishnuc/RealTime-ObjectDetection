from django.urls import path
from . import views 
from django.conf.urls.static import static
from django.conf import settings
from .views import ObjectDetectionAPI, SwitchModelAPI, ConfidenceThresholdAPI



urlpatterns = [
    path('', views.home, name='home'), 
    path('upload', views.upload, name='upload'), 
    path('login/', views.user_login, name='user_login'), 
    path('logout/', views.user_logout, name='user_logout'), 
    path('register', views.user_register, name='register'), 
    path('upload_image', views.upload_image, name='upload_image'),  
    path('stream_video', views.stream_video, name='stream_video'), 
    path('live_stream', views.live_stream, name='live_stream'), 
    path('settings', views.settings_page, name='settings'),  
    path('update_settings', views.update_settings, name='update_settings'),  
    path('download/<str:file_type>/<str:filename>/', views.download_file, name='download_file'),
    path('upload-dataset', views.upload_dataset, name='upload_dataset'),
    path('train-model/', views.train_model, name='train_model'),
    path('upload_video', views.upload_video, name='upload_video'),



    #api urls
    path('api/detect/', ObjectDetectionAPI.as_view(), name='api_detect'),
    path('api/switch_model/', SwitchModelAPI.as_view(), name='api_switch_model'),
    path('api/update_confidence/', ConfidenceThresholdAPI.as_view(), name='api_update_confidence'),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)