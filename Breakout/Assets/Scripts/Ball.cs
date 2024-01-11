using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;

public class Ball : MonoBehaviour
{
    public Rigidbody2D rb { get; private set; } // wykorzystywany do kontroli ruchu piłki
    public float speed; // parametr prędkości, publiczny aby można go ustawić w edytorze Unity

    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
        Reset();
    }
    private void Launch()
    {
        Vector2 force = new Vector2(0, -1f); 
        rb.AddForce(force.normalized * speed); // nadaje piłce ruch bezpośrednio w dół z prędkością wyznaczoną przez parametr speed
    }

    public void Reset() 
    {
        rb.velocity = Vector2.zero; // zatrzymuje ruch piłki
        transform.position = Vector2.zero; // ustawia pozycje piłki na (0,0)
        Invoke(nameof(Launch), 3f); // wywołuje funkcję Launch() z 3 sekundowym opźnieniem, żeby rozgrywka nie zaczynała się natychmiastowo, tak aby gracz mógł się przygotować
    }

    private void FixedUpdate()
    {
        rb.velocity = rb.velocity.normalized * speed; // dba o to aby piłka nie spowalniała podczas dłuższej rozgrywki, ani nie przyspieszała zaraz po odbiciu
    }

}
