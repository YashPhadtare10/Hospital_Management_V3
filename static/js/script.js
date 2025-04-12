$(document).ready(function() {
    // Initialize all modals properly
    $('.modal').modal({
        backdrop: 'static',
        keyboard: false,
        show: false
    });

    // Doctor Time Slot Management
    $('#doctor_id, #date').on('change', function() {
        const doctorId = $('#doctor_id').val();
        const date = $('#date').val();
        
        if (doctorId && date) {
            $('#time_slots').html('<div class="text-center py-3"><div class="spinner-border text-primary" role="status"></div> Loading slots...</div>');
            
            $.getJSON(`/admin/get_doctor_slots/${doctorId}/${date}`)
                .done(function(data) {
                    if (data.error) {
                        $('#time_slots').html(`<div class="alert alert-danger">${data.error}</div>`);
                        return;
                    }
                    
                    let html = '<div class="row g-2">';
                    data.slots.forEach(slot => {
                        const isBooked = data.booked_slots.includes(slot.start);
                        html += `
                            <div class="col-md-3 col-6">
                                <div class="slot p-2 text-center rounded ${isBooked ? 'booked bg-light text-muted' : 'bg-light cursor-pointer hover:bg-primary-light'}" 
                                     data-start="${slot.start}" ${isBooked ? '' : 'onclick="selectSlot(this)"'}>
                                    <div class="fw-bold">${slot.start}</div>
                                    <small class="text-muted">${slot.end}</small>
                                    ${isBooked ? '<div class="small text-danger mt-1">Booked</div>' : ''}
                                </div>
                            </div>
                        `;
                    });
                    html += '</div>';
                    $('#time_slots').html(html);
                })
                .fail(function() {
                    $('#time_slots').html('<div class="alert alert-danger">Error loading time slots</div>');
                });
        }
    });

    // Form Validation for Credentials
    $('form[id^="credentialForm"]').on('submit', function(e) {
        const form = $(this);
        const username = form.find('input[name="username"]');
        const password = form.find('input[name="password"]');
        let isValid = true;

        // Validate username
        if (username.val().length < 4 || !/^[a-zA-Z0-9_]+$/.test(username.val())) {
            username.addClass('is-invalid');
            isValid = false;
        } else {
            username.removeClass('is-invalid').addClass('is-valid');
        }

        // Validate password
        if (password.val().length < 8) {
            password.addClass('is-invalid');
            isValid = false;
        } else {
            password.removeClass('is-invalid').addClass('is-valid');
        }

        if (!isValid) {
            e.preventDefault();
            form.addClass('was-validated');
        } else {
            // Show loading state
            form.find('button[type="submit"]')
                .prop('disabled', true)
                .html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...');
        }
    });

    // Real-time validation
    $('input[name="username"]').on('input', function() {
        const input = $(this);
        if (input.val().length >= 4 && /^[a-zA-Z0-9_]+$/.test(input.val())) {
            input.removeClass('is-invalid').addClass('is-valid');
        } else {
            input.removeClass('is-valid');
        }
    });

    $('input[name="password"]').on('input', function() {
        const input = $(this);
        if (input.val().length >= 8) {
            input.removeClass('is-invalid').addClass('is-valid');
        } else {
            input.removeClass('is-valid');
        }
    });

    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip({
        trigger: 'hover'
    });

    // Close modal when clicking outside
    $('.modal').on('click', function(e) {
        if ($(e.target).hasClass('modal')) {
            $(this).modal('hide');
        }
    });

    // Prescription Form Handling
    if ($('#prescriptionForm').length) {
        let medicineCount = $('.medicine-entry').length || 1;
        
        // Add new medicine entry
        $('#addMedicine').click(function() {
            medicineCount++;
            const newEntry = $('#medicineTemplate').html().replace(/{idx}/g, medicineCount);
            $('#medicinesContainer').append(newEntry);
            $('#medicineCount').val(medicineCount);
        });
        
        // Remove medicine entry
        $(document).on('click', '.remove-medicine', function() {
            if ($('.medicine-entry').length > 1) {
                $(this).closest('.medicine-entry').remove();
                medicineCount--;
                $('#medicineCount').val(medicineCount);
            } else {
                alert('At least one medicine is required');
            }
        });
        
        // Form validation
        $('#prescriptionForm').submit(function(e) {
            let valid = true;
            $('.medicine-entry').each(function() {
                const inputs = $(this).find('input[required], select[required]');
                inputs.each(function() {
                    if (!$(this).val()) {
                        $(this).addClass('is-invalid');
                        valid = false;
                    } else {
                        $(this).removeClass('is-invalid');
                    }
                });
            });
            
            if (!$('#diagnosis').val()) {
                $('#diagnosis').addClass('is-invalid');
                valid = false;
            } else {
                $('#diagnosis').removeClass('is-invalid');
            }
            
            if (!valid) {
                e.preventDefault();
                if (!$('#validationAlert').length) {
                    const alert = $(`
                        <div id="validationAlert" class="alert alert-danger alert-dismissible fade show" role="alert">
                            <strong>Missing Information!</strong> Please fill all required fields marked in red.
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    `);
                    $(this).prepend(alert);
                }
                
                // Scroll to first error
                $('html, body').animate({
                    scrollTop: $('.is-invalid').first().offset().top - 100
                }, 500);
            } else {
                // Add medicine count to form
                $(this).append(`<input type="hidden" name="medicine_count" value="${medicineCount}">`);
            }
        });
    }

    // Show/hide break time fields based on checkbox
    $('[id^="hasBreak"]').each(function() {
        const day = this.id.replace('hasBreak', '');
        const breakTimeDiv = $(`#breakTime${day}`);
        
        $(this).on('change', function() {
            breakTimeDiv.css('display', this.checked ? 'block' : 'none');
        });
    });

    // Handle print button
    $('.print-btn').click(function() {
        window.print();
    });
});

// Global function for slot selection
function selectSlot(element) {
    $('.slot').removeClass('selected bg-primary text-white');
    $(element).addClass('selected bg-primary text-white');
    $('#time_slot').val($(element).data('start'));
}

// Binary search implementation for patients
function binarySearchPatients(patients, searchTerm) {
    let left = 0;
    let right = patients.length - 1;
    
    while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        const patientName = patients[mid].name.toLowerCase();
        
        if (patientName === searchTerm.toLowerCase()) {
            return patients[mid];
        } else if (patientName < searchTerm.toLowerCase()) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    
    return null;
}