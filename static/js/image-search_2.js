let searchStream = null;

function startImageSearch() {
    const modal = new bootstrap.Modal(document.getElementById('image-search-modal'));
    const video = document.getElementById('search-video');
    
    modal.show();
    
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(function(mediaStream) {
            searchStream = mediaStream;
            video.srcObject = mediaStream;
        })
        .catch(function(err) {
            alert('ไม่สามารถเข้าถึงกล้องได้');
        });
    
    document.getElementById('image-search-modal').addEventListener('hidden.bs.modal', function() {
        if (searchStream) {
            searchStream.getTracks().forEach(track => track.stop());
        }
    });
}

function captureAndSearch() {
    const video = document.getElementById('search-video');
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);
    
    canvas.toBlob(function(blob) {
        searchProductByImage(blob);
    }, 'image/jpeg', 0.8);
}

async function searchProductByImage(imageBlob) {
    const formData = new FormData();
    formData.append('image', imageBlob, 'search-image.jpg');
    
    try {
        const response = await fetch('/search_by_image', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        displaySearchResults(result);
    } catch (error) {
        alert('เกิดข้อผิดพลาดในการค้นหา');
    }
}

function displaySearchResults(results) {
    const resultsDiv = document.getElementById('search-results');
    
    if (results.length === 0) {
        resultsDiv.innerHTML = '<div class="alert alert-warning">ไม่พบสินค้าที่ตรงกัน</div>';
        return;
    }
    
    let html = '<div class="row">';
    results.forEach(product => {
        html += `
            <div class="col-md-6 mb-2">
                <div class="card" onclick="selectProduct(${product.id})" style="cursor: pointer;">
                    <div class="card-body p-2">
                        <h6 class="card-title mb-1">${product.name}</h6>
                        <small class="text-muted">${product.barcode}</small>
                        <div class="text-end">
                            <span class="badge bg-info">คล้ายกัน ${product.similarity}%</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    resultsDiv.innerHTML = html;
}

function selectProduct(productId) {
    const productSelect = document.getElementById('product_id');
    productSelect.value = productId;
    productSelect.dispatchEvent(new Event('change'));
    
    bootstrap.Modal.getInstance(document.getElementById('image-search-modal')).hide();
    document.getElementById('quantity').focus();
}