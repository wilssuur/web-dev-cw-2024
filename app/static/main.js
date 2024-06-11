"use dtrict"

function fillModal(event) {
    let deleteUrl = event.relatedTarget.dataset.deleteUrl;
    let modalForm = event.target.querySelector("form");
    modalForm.action = deleteUrl;
}

function imagePreviewHandler(event) {
    if (event.target.files && event.target.files[0]) {
        let reader = new FileReader();
        reader.onload = function (e) {
            let img = document.querySelector('.background-preview > img');
            img.src = e.target.result;
            if (img.classList.contains('d-none')) {
                let label = document.querySelector('.background-preview > label');
                label.classList.add('d-none');
                img.classList.remove('d-none');
            }
        }
        reader.readAsDataURL(event.target.files[0]);
    }
}


window.onload = function() {
    let deleteModal = document.getElementById("delete-modal");
    let background_img_field = document.getElementById('file');

    console.log(background_img_field)
    if (background_img_field) {
        background_img_field.onchange = imagePreviewHandler;
    }
    deleteModal.addEventListener("show.bs.modal", fillModal);
}

