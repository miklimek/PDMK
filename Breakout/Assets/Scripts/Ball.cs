using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;

public class Ball : MonoBehaviour
{
    public Rigidbody2D rb { get; private set; }
    public float speed;

    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
        Reset();
    }
    private void Launch()
    {
        Vector2 force = new Vector2(0, -1f);
        rb.AddForce(force.normalized * speed);
    }

    public void Reset()
    {
        rb.velocity = Vector2.zero;
        transform.position = Vector2.zero;
        Invoke(nameof(Launch), 3f);
    }

    private void FixedUpdate()
    {
        rb.velocity = rb.velocity.normalized * speed;
    }

}
