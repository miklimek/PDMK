using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;

public class PlayerMultimodal : MonoBehaviour
{
    public Rigidbody2D rb { get; private set; }
    public float speed;

    private string tangibleURL = "http://127.0.0.1:81/tangible";
    private string gesturesURL = "http://127.0.0.1:81/gestures";
    private float position;
    private string direction;

    private bool isTangible = false;
    private bool isGestures = false;

    private const int SCREENHALFWIDTH = 12;

    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    private void FixedUpdate()
    {
        StartCoroutine(GetPlayerPosition(tangibleURL));
        StartCoroutine(GetPlayerInput(gesturesURL));

        if (isGestures) // if detecting gestures use that input
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
        else if (Input.GetAxisRaw("Horizontal") != 0) // if detecting keyboard input use that
        {
            rb.velocity = new Vector2(Input.GetAxisRaw("Horizontal") * speed, rb.velocity.y);
        }
        else if(isTangible) // if detecting keyboard input use that
        {
            Vector2 newPosition = new Vector2(SCREENHALFWIDTH * position, rb.position.y);
            float t = Vector2.Distance(rb.position, newPosition) / speed;

            rb.transform.position = Vector2.MoveTowards(rb.position, newPosition, t);
        }
        else // if not detecting input remain in position
        {
            rb.velocity = Vector2.zero;
        }

    }

    IEnumerator GetPlayerPosition(string url)
    {
        UnityWebRequest request = UnityWebRequest.Get(url);

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError(request.error);
            yield break;
        }
        string json = request.downloadHandler.text;

        position = JsonUtility.FromJson<PlayerPositionTangible>(json).position;
        isTangible = JsonUtility.FromJson<PlayerPositionTangible>(json).isNew;
    }

    IEnumerator GetPlayerInput(string url)
    {
        UnityWebRequest request = UnityWebRequest.Get(url);

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError(request.error);
            yield break;
        }
        string json = request.downloadHandler.text;

        direction = JsonUtility.FromJson<PlayerDirectionGestures>(json).direction;
        isGestures = JsonUtility.FromJson<PlayerDirectionGestures>(json).isNew;
    }
}
