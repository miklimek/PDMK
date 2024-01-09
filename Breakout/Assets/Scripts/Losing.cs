using System;
using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.SocialPlatforms.Impl;
using UnityEngine.WSA;

public class Losing : MonoBehaviour
{
    public int health = 5;
    public TextMeshProUGUI lives;

    void Start()
    {
        lives.text = "Lives: " + health.ToString();
    }

    private void OnCollisionEnter2D(Collision2D collision)
    {
        if (collision.gameObject.name != "Ball")
            return;

        health -= 1;
        if (health > 0)
        {
            lives.text = "Lives: " + health.ToString();
            Ball ball = collision.gameObject.GetComponent<Ball>();
            ball.rb.MovePosition(new Vector2(0, 0));
            ball.Reset();
        }
        else
        {
            SceneManager.LoadScene("GameOver");  
        }

    }
}
