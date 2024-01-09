using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;

public class Block : MonoBehaviour
{
    public SpriteRenderer sprite { get; private set; }
    public Sprite[] states;

    private const int MAXPOINTS = 9000;
    public int points = 100;
    public TextMeshProUGUI score;
    public int health { get; private set; }

    void Start()
    {
        sprite = GetComponent<SpriteRenderer>();
        health = states.Length;
        sprite.sprite = states[health - 1];
    }

    private void OnCollisionEnter2D(Collision2D collision)
    {
        if (collision.gameObject.name != "Ball")
            return;

        health -= 1;
        if (health > 0)
            sprite.sprite = states[health - 1];
        else
            gameObject.SetActive(false);

        int current = int.Parse(score.text);
        score.text = (current + points).ToString();

        if(current + points == MAXPOINTS)
        {
            SceneManager.LoadScene("GameComplete");
        }
    }
}
