from importlib import invalidate_caches
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .forms import RegisterForm
from .forms import LoginForm
from .forms import SearchForm
from .models import Movie,User

PAGE_SIZE_PER_CATEGORY = 20
recommended_ids=[]

def index_view(request):
    categories_to_display = ['Action', 'Adventure']
    data = {}
    # Get recommendations from session
    recommended_movies = []
    recommended_ids = request.session.get('recommended_ids', [1,2])
    print("recommendations:",recommended_ids)
    if len(recommended_ids):
        recommended_movies = Movie.objects.filter(id__in=recommended_ids)
        data["Recommended for You"] = recommended_movies[:PAGE_SIZE_PER_CATEGORY]
        request.session['recommended_ids']=[]

    for category_name in categories_to_display:
        movies = Movie.objects.filter(category__name=category_name)
        if request.method == 'POST':
            search_text = request.POST.get('search_text')
            movies = movies.filter(name__icontains=search_text)
        data[category_name] = movies[:20]

    search_form = SearchForm()
    return render(request, 'netflix/index.html', {
        'data': data.items(),
        'search_form': search_form,
        'recommended_movies': recommended_movies
    })

# def new_upd(request):
#     categories_to_display = ['Action', 'Adventure']
#     data = {}
#     # Get recommendations from session
#     recommended_movies = []
#     recommended_ids = request.session.get('recommended_ids', [1,2])
#     print("recommendations:",recommended_ids)
#     if len(recommended_ids):
#         recommended_movies = Movie.objects.filter(id__in=recommended_ids)
#         data["Recommended for You"] = recommended_movies[:PAGE_SIZE_PER_CATEGORY]
#         request.session['recommended_ids']=[]

#     for category_name in categories_to_display:
#         movies = Movie.objects.filter(category__name=category_name)
#         if request.method == 'POST':
#             search_text = request.POST.get('search_text')
#             movies = movies.filter(name__icontains=search_text)
#         data[category_name] = movies[:PAGE_SIZE_PER_CATEGORY]


#     search_form = SearchForm()
#     return render(request, 'netflix/index.html', {
#         'data': data.items(),
#         'search_form': search_form,
#         'recommended_movies': recommended_movies
#     })


def watch_movie_view(request):
    """Watch view."""
    # The primary key of the movie the user want to watch is sent by GET parameters.
    # We retrieve that pk.
    movie_pk = request.GET.get('movie_pk')
    # We try to get from the database the movie with the given pk 
    try:
        movie = Movie.objects.get(pk=movie_pk)
    except Movie.DoesNotExist:
        # if that movie doesn't exist, Movie.DoesNotExist exception is raised
        # and we then catch it and set the url to None instead
        movie = None
    return render(request, 'netflix/watch_movie.html', {'movie': movie})


def register_view(request):
    """Registration view."""
    if request.method == 'GET':
        # executed to render the registration page
        register_form = RegisterForm()
        return render(request, 'netflix/register.html', locals())
    else:
        # executed on registration form submission
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            User.objects.create(
                first_name=request.POST.get('firstname'),
                last_name=request.POST.get('lastname'),
                email=request.POST.get('email'),
                username=request.POST.get('email'),
                password=make_password(request.POST.get('password'))
            )
            return HttpResponseRedirect('/login')
        return render(request, 'netflix/register.html', locals())


def login_view(request):
    """Login view."""
    if request.method == 'GET':
        # executed to render the login page
        login_form = LoginForm()
        return render(request, 'netflix/login.html', locals())
    else:
        # get user credentials input
        username = request.POST['email']
        password = request.POST['password']
        # If the email provided by user exists and match the
        # password he provided, then we authenticate him.
        user = authenticate(username=username, password=password)
        if user is not None:
            # if the credentials are good, we login the user
            login(request, user)
            # then we redirect him to home page
            return HttpResponseRedirect('/')
        # if the credentials are wrong, we redirect him to login and let him know
        return render(
            request,
            'netflix/login.html',
            {
                'wrong_credentials': True,
                'login_form': LoginForm(request.POST)
            }
        )

def logout_view(request):
    """Logout view."""
    # logout the request
    logout(request)
    # redirect user to home page
    return HttpResponseRedirect('/')


# @csrf_exempt
# def chatbot_response(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         user_message = data.get('message', '').lower()

#         # Dummy logic – replace with ML/NLP or database-based logic
#         if "sci-fi" in user_message:
#             recommendations = ["Stranger Things", "Dark", "Lost in Space"]
#             response = "You seem to like sci-fi! Here are some picks:"
#         else:
#             recommendations = ["The Crown", "Breaking Bad", "Money Heist"]
#             response = "Here are some popular shows you might like."

#         return JsonResponse({"response": response, "recommendations": recommendations})
import requests
import sys
API_URL = "http://localhost:8001/chat"

@csrf_exempt
def chatbot_response(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body)
        payload= {"query": data.get("message", ""), "thread_id": data.get("thread_id", "1")}
        print(payload)
        fastapi_response = requests.post(
            API_URL,
            json=payload
        )
        fastapi_response.raise_for_status()

        # Extract full JSON from FastAPI
        result = fastapi_response.json()
        response_text = result.get("response", "Error: No response field found.")
        print("response: ",response_text,"\n\n\n\n")
        movies=result.get("movies",[])
        recommendations = []  # You can populate this dynamically
        titles=[]
        for movie in movies:
            title=movie.get("title","").strip().strip('*').strip('-')
            # rating=movie.get("imdb_rating","8.0")
            # year= movie.get("year",0)
            # description=movie.get("description")[27:] if len(description)
            # length= int(movie.get("runtime",0))
            print(title," ")
            op,created=Movie.objects.get_or_create(name=title)
            # if not movie:
            #     movie=Movie.objects.create(name=title)
            titles.append(str(title))
            recommendations.append(op.id)

        request.session['recommended_ids'] = recommendations
        user,created=User.objects.get_or_create(id=5,age=20)
        user.recommended_ids=recommendations
        # recommended_ids=recommendations
        next_question=result.get("next_question","")
        # Optional: fetch recommendations from DB or return dummy
        print({
            "response": response_text,
            "recommendations": [],
            "titles":"\n".join(titles)
        })
        return JsonResponse({
            "response": response_text,
            "recommendations": [],
            "next_question": next_question,
            "titles": "\n".join(titles)
        })

    except requests.exceptions.ConnectionError:
        print(f"\nError: Could not connect to the API server at {API_URL}")
        return JsonResponse({
            "response": "Error: Could not connect to the FastAPI server.",
            "recommendations": []
        }, status=500)

    except requests.exceptions.RequestException as e:
        print(f"\nError during API request: {e}")
        return JsonResponse({
            "response": f"Error communicating with FastAPI: {str(e)}",
            "recommendations": []
        }, status=500)

    except Exception as e:
        return JsonResponse({
            "response": f"Unexpected error: {str(e)}",
            "recommendations": []
        }, status=500)

    # try:
    #     data = json.loads(request.body)
    #     query = data.get("query")
    #     thread_id = data.get("thread_id")

    #     if not query or not thread_id:
    #         return JsonResponse({'error': 'Missing query or thread_id'}, status=400)

    #     config = {"configurable": {"thread_id": thread_id}}
    #     inputs = {"messages": [HumanMessage(content=query)]}
    #     final_response_message = "Sorry, I couldn't generate a response."

    #     final_state_event = None
    #     for event in graph.stream(inputs, config=config, stream_mode="values"):
    #         final_state_event = event

    #     if final_state_event and 'messages' in final_state_event:
    #         ai_messages = [msg for msg in final_state_event['messages'] if isinstance(msg, AIMessage)]
    #         if ai_messages:
    #             final_response_message = ai_messages[-1].content

    #     return JsonResponse({"response": final_response_message})

    except Exception as e:
        print(f"Error in Django chat endpoint for thread {data.get('thread_id', 'N/A')}: {e}")
        return JsonResponse({"response": f"An error occurred: {str(e)}"})