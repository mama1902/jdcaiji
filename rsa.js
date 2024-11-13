
function decodeURI(text) {
	text =  decodeURIComponent(text);
	text = text.replace('¥', '');
	return text;
}

function findelements(y, text) {
	var i;
	for (i = 0; i < y.length; i++) {
		if (y[i].innerText == text) {
			y[i].click();
			return true;
		}
	}
	return false;
}
