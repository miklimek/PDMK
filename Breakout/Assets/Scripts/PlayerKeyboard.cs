using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class PlayerKeyboard : MonoBehaviour
{
    public Rigidbody2D rb { get; private set; } // potrzebny do kontroli ruchu gracza
    public float speed; // parametr prędkości, ustawiany w edytorze Unity

    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    private void FixedUpdate()
    {
        rb.velocity = new Vector2(Input.GetAxisRaw("Horizontal") * speed, rb.velocity.y); // zmień wektor prędkości gracza na zgodny z kierunkiem strzałek (prawo - lewo)
    }
}
