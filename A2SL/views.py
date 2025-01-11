from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk
from django.contrib.staticfiles import finders
from django.contrib.auth.decorators import login_required

# Download required NLTK data
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')

def home_view(request):
    return render(request, 'home.html')

def about_view(request):
    return render(request, 'about.html')

def contact_view(request):
    return render(request, 'contact.html')

@login_required(login_url="login")
def animation_view(request):
    if request.method == 'POST':
        text = request.POST.get('sen', '').strip()
        if not text:
            return render(request, 'animation.html', {'words': [], 'text': text})

        # Tokenizing and processing the input text
        text = text.lower()
        words = word_tokenize(text)
        tagged = nltk.pos_tag(words)

        # Identify tense
        tense = {
            "future": len([word for word in tagged if word[1] == "MD"]),
            "present": len([word for word in tagged if word[1] in ["VBP", "VBZ", "VBG"]]),
            "past": len([word for word in tagged if word[1] in ["VBD", "VBN"]]),
            "present_continuous": len([word for word in tagged if word[1] == "VBG"]),
        }

        # Define stop words and initialize lemmatizer
        stop_words = set(stopwords.words('english'))
        lr = WordNetLemmatizer()

        # Process words: Remove stopwords and apply lemmatization
        filtered_text = [
            lr.lemmatize(w, pos='v') if p[1] in ['VBG', 'VBD', 'VBZ', 'VBN', 'NN'] else 
            lr.lemmatize(w, pos='a') if p[1] in ['JJ', 'JJR', 'JJS', 'RBR', 'RBS'] else 
            lr.lemmatize(w)
            for w, p in zip(words, tagged) if w not in stop_words
        ]

        # Adjust words based on tense
        words = ["Me" if w == "I" else w for w in filtered_text]
        probable_tense = max(tense, key=tense.get)

        if probable_tense == "past" and tense["past"] >= 1:
            words = ["Before"] + words
        elif probable_tense == "future" and tense["future"] >= 1 and "Will" not in words:
            words = ["Will"] + words
        elif probable_tense == "present" and tense["present_continuous"] >= 1:
            words = ["Now"] + words

        # Check for animation file availability
        final_words = []
        for w in words:
            path = w + ".mp4"
            if finders.find(path):
                final_words.append(w)
            else:
                # If word animation not found, add single letters
                final_words.extend(list(w))
        words = final_words

        # Render the final animation view
        return render(request, 'animation.html', {'words': words, 'text': text})
    else:
        return render(request, 'animation.html')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('animation')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(request.POST.get('next', 'animation'))
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect("home")
