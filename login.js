document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const username = document.querySelector('[name="username"]').value;
    const password = document.querySelector('[name="password"]').value;
    
    console.log("Logging in with:", username, password);
     window.location.href = 'records.html';
});
