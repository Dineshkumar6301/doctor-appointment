// doctor_calendar.js - Place this in your static/js directory

$(document).ready(function() {
    // Initialize the calendar
    if ($("#appoinment_calendar").length) {
        initializeCalendar();
    }

    // Connect Add Event button click
    $(".btn-box a.theme-btn-one").on("click", function(e) {
        e.preventDefault();
        window.location.href = '/add_event/';
    });
});

function initializeCalendar() {
    // Initialize calendar with FullCalendar
    const calendar = new FullCalendar.Calendar(document.getElementById('appoinment_calendar'), {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: '/get_events/',
        selectable: true,
        editable: true,
        eventClick: function(info) {
            // When an event is clicked, redirect to edit page
            window.location.href = '/edit_event/' + info.event.id + '/';
        },
        select: function(info) {
            // When a date range is selected, open add event page with pre-populated dates
            const startDate = moment(info.start).format('YYYY-MM-DDTHH:mm');
            const endDate = moment(info.end).format('YYYY-MM-DDTHH:mm');
            window.location.href = `/add_event/?start=${startDate}&end=${endDate}`;
        },
        eventDrop: function(info) {
            // When an event is dragged and dropped
            updateEventTime(
                info.event.id,
                moment(info.event.start).format('YYYY-MM-DD HH:mm:ss'),
                moment(info.event.end).format('YYYY-MM-DD HH:mm:ss')
            );
        },
        eventResize: function(info) {
            // When an event is resized
            updateEventTime(
                info.event.id,
                moment(info.event.start).format('YYYY-MM-DD HH:mm:ss'),
                moment(info.event.end).format('YYYY-MM-DD HH:mm:ss')
            );
        }
    });
    
    calendar.render();
    
    // Connect view switcher buttons
    $('.date-zone li a').on('click', function(e) {
        e.preventDefault();
        const view = $(this).text().toLowerCase();
        
        if (view === 'month') {
            calendar.changeView('dayGridMonth');
        } else if (view === 'week') {
            calendar.changeView('timeGridWeek');
        } else if (view === 'day') {
            calendar.changeView('timeGridDay');
        }
    });
    
    // Connect today button
    $('.today-box a').on('click', function(e) {
        e.preventDefault();
        calendar.today();
    });
}

function updateEventTime(eventId, startTime, endTime) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/update_event_ajax/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            id: eventId,
            start: startTime,
            end: endTime
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status !== 'success') {
            alert('Failed to update event. Please try again.');
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the event.');
        window.location.reload();
    });
}