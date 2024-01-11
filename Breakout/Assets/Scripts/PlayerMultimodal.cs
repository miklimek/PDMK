using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;

public class PlayerMultimodal : MonoBehaviour
{
    public Rigidbody2D rb { get; private set; } // potrzebny do kontroli ruchu gracza
    public float speed; // parametr prędkości, ustawiany w edytorze Unity

    private string tangibleURL = "http://127.0.0.1:81/tangible"; // link do endpoitu serwera API dla tangible interface
    private string gesturesURL = "http://127.0.0.1:81/gestures"; // link dla gestów
    private float position; // pozycja gracza
    private string direction; // kierunek gracza

    private bool isTangible = false; // czy dostępne są nowe dane tangible
    private bool isGestures = false; // czy dostępne są nowe dane gestów

    private const int SCREENHALFWIDTH = 12; // stała określająca połowę szerokości ekranu

    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    private void FixedUpdate()
    {
        // pobierz dane z serwera API
        StartCoroutine(GetPlayerPosition(tangibleURL));
        StartCoroutine(GetPlayerInput(gesturesURL));

        if (isGestures) // jeśli dane o gestach są nowe to wykorzystaj je do sterowania
        {
            if (direction == "Stop")
            {
                rb.velocity = new Vector2(0, rb.velocity.y);
            }
            else if (direction == "Left")
            {
                rb.velocity = new Vector2(-1 * speed, rb.velocity.y);
            }
            else if (direction == "Right")
            {
                rb.velocity = new Vector2(1 * speed, rb.velocity.y);
            }
        }
        else if (Input.GetAxisRaw("Horizontal") != 0) // jeśli wykrywane jest wejście z klawiatury to wykorzystaj je do sterowania
        {
            rb.velocity = new Vector2(Input.GetAxisRaw("Horizontal") * speed, rb.velocity.y);
        }
        else if(isTangible) // jeśli dane o pozycji obiektu są nowe to wykorzystaj je do sterowania
        {
            Vector2 newPosition = new Vector2(SCREENHALFWIDTH * position, rb.position.y);
            float t = Vector2.Distance(rb.position, newPosition) / speed;

            rb.transform.position = Vector2.MoveTowards(rb.position, newPosition, t);
        }
        else // jeśli nie wykrywane są nowe dane wejściowe to gracz nie porusza się
        {
            rb.velocity = Vector2.zero;
        }

    }

    IEnumerator GetPlayerPosition(string url) // pobieranie danych z serwera dla tangible interface
    {
        UnityWebRequest request = UnityWebRequest.Get(url); // utwórz nowe żądanie HTTP typu GET

        yield return request.SendWebRequest(); // wyślij żadanie i czekaj na odpowiedź

        if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError(request.error); // w przypadku błędów żadania wypisz błąd w konsoli i zakończ działanie funkcji
            yield break;
        }
        string json = request.downloadHandler.text; // dane z API w formacie JSON

        position = JsonUtility.FromJson<PlayerPositionTangible>(json).position; // przetworzenie danych JSON na obiekt klasy PlayerPositionTangible i pobranie wartości o pozycji
        isTangible = JsonUtility.FromJson<PlayerPositionTangible>(json).isNew; // pobranie wartości nowo�ci pomiaru z danych JSON
    }

    IEnumerator GetPlayerInput(string url) // pobieranie danych z serwera dla gestów
    {
        UnityWebRequest request = UnityWebRequest.Get(url); // utwórz żądanie HTTP typu GET

        yield return request.SendWebRequest(); // wyślij żadanie i czekaj na odpowiedź

        if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError(request.error); // w przypadku błędów żadania wypisz błąd w konsoli i zakończ działanie funkcji
            yield break;
        }
        string json = request.downloadHandler.text; // dane z API w formacie JSON

        direction = JsonUtility.FromJson<PlayerDirectionGestures>(json).direction; // przetworzenie danych JSON na obiekt klasy PlayerDirectionGestures i pobranie wartości o kierunku
        isGestures = JsonUtility.FromJson<PlayerDirectionGestures>(json).isNew; // pobranie wartości nowo�ci pomiaru z danych JSON
    }
}
