using System;
using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;

public class PlayerTangible : MonoBehaviour
{
    public Rigidbody2D rb { get; private set; } // potrzebny do kontroli ruchu gracza
    public float speed; // parametr prędkości, ustawiany w edytorze Unity

    private string url = "http://127.0.0.1:81/tangible"; // adres endpointu API do pobierania danych
    private float position; // aktualna pozycja gracza

    private const int SCREENHALFWIDTH = 12; // stała określająca połowę szerokości ekranu gry

    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    private void FixedUpdate()
    {
        StartCoroutine(GetPlayerPosition(url)); // pobierz dane z API
        Vector2 newPosition = new Vector2(SCREENHALFWIDTH * position, rb.position.y); // ustal nową pozycje gracza zgodnie z przemieszczeniem (połowa szerokości ekranu * pozycja obiektu)
        float t = Vector2.Distance(rb.position, newPosition) / speed; // czas w jakim gracz ma się przemieścić z aktualnej pozycji do nowej t = s/v

        rb.transform.position = Vector2.MoveTowards(rb.position, newPosition, t); // przemieść gracza do nowej pozycji w czasie t
        //rb.transform.position = Vector2.MoveTowards(rb.position, newPosition, speed * Time.deltaTime);
    }

    IEnumerator GetPlayerPosition(string url)
    {
        UnityWebRequest request = UnityWebRequest.Get(url); // utwórz żądanie HTTP typu GET

        yield return request.SendWebRequest(); // wyślij żadanie i czekaj na odpowiedź

        if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError(request.error); // w przypadku błędów żadania wypisz błąd w konsoli i zakończ działanie funkcji
            yield break;
        }
        string json = request.downloadHandler.text; // dane z API w formacie JSON

        position = JsonUtility.FromJson<PlayerPositionTangible>(json).position; // przetworzenie danych JSON na obiekt klasy PlayerPositionTangible i pobranie wartości o pozycji
    }
}
