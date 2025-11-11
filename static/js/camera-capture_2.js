let stream = null;
let canvas = null;

function startCamera() {
    const modal = new bootstrap.Modal(document.getElementById('camera-modal'));
    const video = document.getElementById('camera-video');
    
    modal.show();
    
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(function(mediaStream) {
            stream = mediaStream;
            video.srcObject = stream;
        })
        .catch(function(err) {
            alert('ไม่สามารถเข้าถึงกล้องได้');
        });
    
    document.getElementById('camera-modal').addEventListener('hidden.bs.modal', function() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });
}

function capturePhoto() {
    const video = document.getElementById('camera-video');
    canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);
    
    canvas.toBlob(function(blob) {
        const file = new File([blob], 'captured-image.jpg', { type: 'image/jpeg' });
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        
        const fileInput = document.querySelector('input[name="image"]');
        fileInput.files = dataTransfer.files;
        
        // Show preview
        const preview = document.getElementById('image-preview');
        if (preview) {
            preview.src = canvas.toDataURL();
            preview.style.display = 'block';
        }
        
        bootstrap.Modal.getInstance(document.getElementById('camera-modal')).hide();
    }, 'image/jpeg', 0.8);
}