using System;
using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.SocialPlatforms.Impl;
using UnityEngine.WSA;

public class Losing : MonoBehaviour // skrypt dotyczy dolnej ściany gry, odpowiada za punkty życia gracza i zakończenie rozgrywki
{
    public int health = 5; // liczba żyć gracza, domyślnie 5, możliwe do edycji w edytorze Unity
    public TextMeshProUGUI lives; // tekst wyświetlający aktualna liczbę żyć gracza

    void Start()
    {
        lives.text = "Lives: " + health.ToString(); // ustaw tekst na wyświetlanie ustalonej liczby żyć (dynamicznie bo może być zmieniony w edytorze Unity)
    }

    private void OnCollisionEnter2D(Collision2D collision)
    {
        if (collision.gameObject.name != "Ball") // bierzemy pod uwagę tylko zderzenia z piłką
            return;

        health -= 1;
        if (health > 0) // jeśli pozostały punkty życia to:
        {
            lives.text = "Lives: " + health.ToString(); // pokaż nową liczbę punktów życia na ekranie
            Ball ball = collision.gameObject.GetComponent<Ball>();
            ball.rb.MovePosition(new Vector2(0, 0)); // przesuń piłkę do punktu (0,0)
            ball.Reset(); // wywołaj funkcję resetującą zachowanie piłki, funkcja opisana w pliku Ball
        }
        else
        {
            SceneManager.LoadScene("GameOver"); // jeśli stracono wszystkie punkty życiaa do zakończ grę (przejdź do ekranu przegranej)
        }

    }
}
