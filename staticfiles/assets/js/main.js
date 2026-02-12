$(document).ready(function () {
    // Modal Toggle for Registration
    const registerModal = $('#registerModal');
    const loginModal = $('#loginModal');
    const closeRegisterModal = $('#closeRegisterModal');
    const closeLoginModal = $('#closeLoginModal');
    const joinNowBtn = $('.theme-btn-one[data-target="#registerModal"]');
    const signInBtn = $('a[data-target="#loginModal"]');

    joinNowBtn.on('click', function (e) {
        e.preventDefault();
        registerModal.css('display', 'block');
        loginModal.css('display', 'none');
    });

    signInBtn.on('click', function (e) {
        e.preventDefault();
        loginModal.css('display', 'block');
        registerModal.css('display', 'none');
    });

    closeRegisterModal.on('click', function () {
        registerModal.css('display', 'none');
    });

    closeLoginModal.on('click', function () {
        loginModal.css('display', 'none');
    });

    // Close modals when clicking outside
    $(window).on('click', function (e) {
        if (e.target.id === 'registerModal') {
            registerModal.css('display', 'none');
        }
        if (e.target.id === 'loginModal') {
            loginModal.css('display', 'none');
        }
    });

    // Show/Hide Doctor Fields based on User Type
    $('#userType').on('change', function () {
        if ($(this).val() === 'doctor') {
            $('#doctorFields').show();
            $('#specialization, #licenseNumber').attr('required', true);
        } else {
            $('#doctorFields').hide();
            $('#specialization, #licenseNumber').removeAttr('required');
        }
    });

    // Registration Form Submission
    $('#registerForm').on('submit', function (e) {
        e.preventDefault();
        const formData = {
            userType: $('#userType').val(),
            firstName: $('#firstName').val(),
            lastName: $('#lastName').val(),
            email: $('#email').val(),
            password: $('#password').val(),
            confirmPassword: $('#confirmPassword').val(),
            specialization: $('#specialization').val(),
            licenseNumber: $('#licenseNumber').val(),
            terms: $('#terms').is(':checked'),
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
        };

        $.ajax({
            url: '/accounts/register/',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function (response) {
                if (response.status === 'success') {
                    alert(response.message);
                    registerModal.css('display', 'none');
                    $('#registerForm')[0].reset();
                    $('#doctorFields').hide();
                    window.location.reload();
                } else {
                    alert('Error: ' + JSON.parse(response.message));
                }
            },
            error: function (xhr) {
                alert('Error: ' + xhr.responseJSON.message);
            }
        });
    });

    // Login Form Submission
    $('#loginForm').on('submit', function (e) {
        e.preventDefault();
        const formData = {
            email: $('#loginEmail').val(),
            password: $('#loginPassword').val(),
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
        };

        $.ajax({
            url: '/accounts/login/',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function (response) {
                if (response.status === 'success') {
                    alert(response.message);
                    loginModal.css('display', 'none');
                    $('#loginForm')[0].reset();
                    window.location.reload();
                } else {
                    alert('Error: ' + JSON.parse(response.message));
                }
            },
            error: function (xhr) {
                alert('Error: ' + xhr.responseJSON.message);
            }
        });
    });

    // Mobile Menu Toggle
    const mobileNavToggler = $('.mobile-nav-toggler');
    const mobileMenu = $('.mobile-menu');
    const menuBackdrop = $('.menu-backdrop');
    const closeBtn = $('.close-btn');

    mobileNavToggler.on('click', function () {
        mobileMenu.addClass('menu-open');
        menuBackdrop.fadeIn();
    });

    closeBtn.on('click', function () {
        mobileMenu.removeClass('menu-open');
        menuBackdrop.fadeOut();
    });

    menuBackdrop.on('click', function () {
        mobileMenu.removeClass('menu-open');
        menuBackdrop.fadeOut();
    });

    // Initialize Owl Carousel
    $('.clients-carousel').owlCarousel({
        loop: true,
        margin: 10,
        nav: false,
        dots: false,
        autoplay: true,
        autoplayTimeout: 3000,
        responsive: {
            0: { items: 2 },
            600: { items: 3 },
            1000: { items: 5 }
        }
    });

    $('.single-item-carousel').owlCarousel({
        loop: true,
        margin: 10,
        nav: true,
        dots: false,
        autoplay: true,
        autoplayTimeout: 5000,
        items: 1,
        navText: ['<i class="fas fa-arrow-left"></i>', '<i class="fas fa-arrow-right"></i>']
    });

    // Initialize WOW.js
    new WOW().init();

    // Sticky Header
    const stickyHeader = $('.sticky-header');
    $(window).on('scroll', function () {
        if ($(this).scrollTop() > 100) {
            stickyHeader.addClass('sticky');
        } else {
            stickyHeader.removeClass('sticky');
        }
    });

    // Scroll to Top
    const scrollTopBtn = $('.scroll-top');
    $(window).on('scroll', function () {
        if ($(this).scrollTop() > 200) {
            scrollTopBtn.fadeIn();
        } else {
            scrollTopBtn.fadeOut();
        }
    });

    scrollTopBtn.on('click', function () {
        $('html, body').animate({ scrollTop: 0 }, 800);
        return false;
    });
});