using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UIElements;

public class PlayerGestures : MonoBehaviour
{
    public Rigidbody2D rb { get; private set; } // potrzebny do kontroli ruchu gracza
    public float speed; // parametr prędkości, ustawiany w edytorze Unity

    private string url = "http://127.0.0.1:81/gestures"; // link do endpointu
    private string direction; // aktualny kierunek paletki

    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
    }
    private void FixedUpdate()
    {
        StartCoroutine(GetPlayerInput(url)); // pobierz dane z serwera API

        // W zależności od kierunku z danych z serwera odpowiednio:
        if (direction == "Stop")
        {
            rb.velocity = new Vector2(0, rb.velocity.y); // jeśli stop - zatrzymaj ruch gracza
        }
        else if (direction == "Left")
        {
            rb.velocity = new Vector2(-1 * speed, rb.velocity.y); // jeśli lewo - zmień kierunek wektora prędkości na ujemny - poruszanie się w lewo
        }
        else if (direction == "Right")
        {
            rb.velocity = new Vector2(1 * speed, rb.velocity.y); // jeśli prawo - zmień kierunek wektora prędkości na dodatni - poruszanie się w prawo
        }
    }

    IEnumerator GetPlayerInput(string url)
    {
        UnityWebRequest request = UnityWebRequest.Get(url); // utwórz żadanie HTTP typu GET

        yield return request.SendWebRequest(); // wyślij żadanie i czekaj na odpowiedź

        if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError(request.error); // w przypadku błędów żadania wypisz błąd w konsoli i zakończ działanie funkcji
            yield break;
        }
        string json = request.downloadHandler.text; // dane z API w formacie JSON

        direction = JsonUtility.FromJson<PlayerDirectionGestures>(json).direction; // przetworzenie danych JSON na obiekt klasy PlayerDirectionGestures i ustawienie kierunku gracza na kierunek obiektu
    }
}
