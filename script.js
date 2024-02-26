window.addEventListener('load', () => {
    const colors = ['#FF5733', '#FFBD33', '#33FF57', '#3388FF', '#FF33E9', '#7F33FF']; // Add your desired colors
    const elements = document.querySelectorAll('.random-color');

    elements.forEach(element => {
        const randomIndex = Math.floor(Math.random() * colors.length);
        const randomColor = colors[randomIndex];
        element.style.color = randomColor;
    });
});
