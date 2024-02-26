window.addEventListener('load', () => {
    const colors = ['#FF5733', '#FFBD33', '#33FF57', '#3388FF', '#FF33E9', '#7F33FF']; // Add your desired colors
    const elements = document.querySelectorAll('.random-color');

    elements.forEach(element => {
        const randomIndexText = Math.floor(Math.random() * colors.length);
        const randomColorText = colors[randomIndexText];
        element.style.color = randomColorText;
        colors.splice(randomIndexText,1);
        const randomIndexBackground = Math.floor(Math.random() * colors.length);
        const randomColorBackground = colors[randomIndexBackground];
        element.setAttribute('style', 'background-color: ' + randomColorBackground + ';');
    });
});

