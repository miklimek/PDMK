using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;

public class Block : MonoBehaviour
{
    public SpriteRenderer sprite { get; private set; } // aktualny sprite bloku
    public Sprite[] states; // lista dostępnych sprite, ustawiana w edytorze Unity, zależna od punktów życia bloku

    private const int MAXPOINTS = 9000; // maksymalna liczba punktów, ustawiana ręcznie na liczbą bloków * 100
    public int points = 100; // punkty za uderzenie w pojedynczy blok
    public TextMeshProUGUI score; // tekst z aktualnym wynikiem punktowym gracza
    public int health { get; private set; } // liczba jużpozostłych "żyć" bloku, ile razy należy uderzyć blok aby zniknął

    void Start()
    {
        sprite = GetComponent<SpriteRenderer>();
        health = states.Length;
        sprite.sprite = states[health - 1];
    }

    private void OnCollisionEnter2D(Collision2D collision)
    {
        if (collision.gameObject.name != "Ball") // bierzemy pod uwagę tylko zderzenia z piłką
            return;

        health -= 1;
        if (health > 0)
            sprite.sprite = states[health - 1]; // zmień sprite bloku zgodnie z liczbą jużpozostłych punktów życia
        else
            gameObject.SetActive(false); // jeśli blok nie ma już punktów życia to powinien "zniknąć", nie wyświetla się sprite i nie są brane pod uwagę zderzenia

        int current = int.Parse(score.text);
        score.text = (current + points).ToString(); // zwiększa się wynik punktowy i wyświetlany jest nowy

        if(current + points == MAXPOINTS)
        {
            SceneManager.LoadScene("GameComplete"); // zakończ grę (przejdź do ekranu zakończenia) jeśli osiągnięto maksymalną liczbą punktów - zbito wszystkie bloki
        }
    }
}
